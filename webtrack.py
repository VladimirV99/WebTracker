import requests
from bs4 import BeautifulSoup
import re
import os
import hashlib
import time
import json
import difflib

import utils


class WebTracker:

    def __init__(self, log_path="logs", log_file_name="log", track_path="track", email_notify=False):
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'}
        self.session = None
        self.hashes = {}
        self.track_path = track_path
        self.log_path = log_path
        self.log_file_name = log_file_name
        self.email_notify = email_notify

        if os.path.isdir(self.track_path):
            for file in os.listdir(self.track_path):
                if file.endswith(".txt"):
                    self.hashes[os.path.splitext(os.path.basename(file))[0]] = self.get_hash_for_file(file)
        else:
            os.mkdir(self.track_path)

        if not os.path.isdir(self.log_path):
            os.mkdir(self.log_path)
        i = 1
        self.log_file_base_name = os.path.join(self.log_path, self.log_file_name + "-" + time.strftime("%Y-%m-%d", time.localtime()) + "-")
        while True:
            if not os.path.exists(self.log_file_base_name + str(i) + ".txt"):
                self.log_file_name = self.log_file_base_name + str(i) + ".txt"
                break
            i = i + 1

        self.log("Tracker Initialized")

    def log(self, message):
        with open(self.log_file_name, "a") as log_file:
            current_time = time.strftime("[%H:%M:%S]", time.localtime())
            log_file.write(current_time + message + "\n")
        print(message)

    def get_hash_for_file(self, filename):
        with open(os.path.join(self.track_path, filename), 'rb') as file:
            return self.get_hash(file.read())

    @staticmethod
    def get_hash(text):
        hasher = hashlib.md5()
        hasher.update(text)
        return hasher.hexdigest()

    def start_session(self):
        self.session = requests.session()
        self.session.headers.update(self.headers)

    def get_session(self):
        return self.session

    def set_headers(self, headers):
        self.headers = headers
        if self.session:
            self.session.headers.update(self.headers)

    def get(self, url, verify=True):
        return self.session.get(url, verify=verify)

    def post(self, url, data, verify=True):
        return self.session.post(url, data=data, verify=verify)

    def get_soup(self, url, verify=True):
        page = self.get(url, verify=verify)
        soup = BeautifulSoup(page.content, 'html.parser')
        return soup

    def check_json(self, filename):
        try:
            diffs = {}
            with open(filename) as file:
                is_logged_in = {}
                json_file = json.load(file)

                mails = []
                if self.email_notify and "notify" in json_file:
                    if "mails" in json_file["notify"]:
                        mails = json_file["notify"]["mails"]

                if "login" in json_file:
                    logins = json_file["login"]
                    for login in logins:
                        try:
                            if "id" not in login:
                                self.log("Login has no id. Skipping")
                                continue
                            login_id = login["id"]
                            is_logged_in[login_id] = False
                            verify_ssl = True
                            page = None
                            payload = None

                            for step in login["steps"]:
                                if "command" not in step:
                                    self.log("Missing command in login '" + login_id + "'. Skipping")
                                    continue

                                if step["command"].lower() == 'verify_ssl':
                                    if step["param"].lower() == 'false':
                                        verify_ssl = False
                                elif step["command"].lower() == 'get':
                                    page = self.get_soup(step["param"], verify=verify_ssl)
                                elif step["command"].lower() == 'post':
                                    res = self.post(step["param"], payload, verify=verify_ssl)
                                    page = BeautifulSoup(res.text, 'html.parser')
                                elif step["command"].lower() == 'select_form':
                                    payload = utils.get_payload(page.select_one(step["param"]))
                                elif step["command"].lower() == 'override_payload':
                                    for payload_key, payload_value in step["param"].items():
                                        payload[utils.decode(payload_key, payload)] = utils.decode(payload_value, payload)

                            if "verify_login" in login:
                                if login["verify_login"] in page.contents:
                                    is_logged_in[login_id] = False
                                else:
                                    is_logged_in[login_id] = True
                            else:
                                is_logged_in[login_id] = True
                                self.log("Warning. Can't confirm login '" + login_id + "'. Assuming success")
                        except KeyError:
                            self.log("Missing key for login. Skipping")
                            continue
                        except requests.exceptions.SSLError:
                            self.log("SSLError, stopping")
                            return False

                if "sites" in json_file:
                    sites = json_file["sites"]
                    for site in sites:
                        try:
                            if "id" not in site:
                                self.log("Site has no id, it can't be tracked. Skipping")
                                continue
                            site_id = site["id"]

                            if "requires" in site:
                                if not is_logged_in[site["requires"].strip()]:
                                    self.log("Missing required login '" + site["requires"].strip() + "' for " + site_id)
                                    continue

                            if "url" not in site:
                                self.log("Missing url for '" + site_id + "'. Skipping")
                                continue
                            url = site["url"]

                            select_element = site.get("select_element", "body")
                            select_attrs = site.get("select_attrs")
                            remove_ids = site.get("remove_ids")
                            remove_classes = site.get("remove_classes")

                            verify = True
                            if "verify_ssl" in site and site["verify_ssl"].lower() == "false":
                                verify = False

                            status, diff = self.track(site_id, url, select_element, select_attrs, remove_ids, remove_classes, verify)
                            if not status:
                                return False
                            if diff is not None:
                                diffs[site_id] = diff

                        except KeyError:
                            self.log("Missing key. Skipping")
                            continue
                        except requests.exceptions.SSLError:
                            self.log("SSLError. Stopping")
                            return False
                else:
                    self.log("No sites to track. Exiting")
                    return False

            if self.email_notify:
                utils.notify(mails, diffs)
        except FileNotFoundError:
            self.log("File Not Found: " + filename)
            return False
        except json.JSONDecodeError:
            self.log("Malformed JSON File " + filename)
            return False
        return True

    def write_track_file(self, site_id, data):
        file = open(os.path.join(self.track_path, site_id + ".txt"), "w")
        file.write(data)
        file.close()

    def track(self, site_id, url, select_element='body', select_attrs=None, remove_ids=None, remove_classes=None, verify_ssl=True):
        try:
            page = self.session.get(url, verify=verify_ssl)
            soup = BeautifulSoup(page.content, 'html.parser')
            if not select_attrs:
                select_attrs = {}
            if not remove_ids:
                remove_ids = {}
            if not remove_classes:
                remove_classes = {}
            body = soup.find(select_element, attrs=select_attrs)
            for script in body(["script", "style"]):
                script.decompose()  # To save the element use extract
            for rm_selector in remove_ids:
                for rm in body.find(id=rm_selector):
                    rm.decompose()
            for rm_selector in remove_classes:
                for rm in body.find_all(class_=rm_selector):
                    rm.decompose()

            res = re.sub(r'\n+', '\n', body.get_text('\n').replace('\t', ''))
            new_hash = self.get_hash(res.encode('utf-8'))

            if site_id in self.hashes:
                if self.hashes[site_id] != new_hash:
                    track_file = open(os.path.join(self.track_path, site_id + ".txt"))

                    message = "'" + site_id + "' has changed\n"
                    diff = ""
                    for line in difflib.unified_diff(track_file.readlines(), res.splitlines(keepends=True), n=2):
                        diff = diff + line
                    diff = diff[:-1]  # Remove final newline
                    message = message + diff

                    self.log(message)

                    self.hashes[site_id] = new_hash
                    self.write_track_file(site_id, res)

                    return True, diff
            else:
                self.hashes[site_id] = new_hash
                self.write_track_file(site_id, res)
        except requests.exceptions.RequestException:
            self.log("Request Error")
            return False, None
        return True, None
