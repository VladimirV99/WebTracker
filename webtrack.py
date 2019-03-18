import requests
from bs4 import BeautifulSoup
import re
import os
import hashlib
import time
import json


class WebTracker:

    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'}
        self.session = None
        self.hashes = {}
        self.track_path = "track"
        self.log_path = "logs"
        self.log_file_name = "log.txt"

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
        hasher = hashlib.md5()
        with open(os.path.join(self.track_path, filename), 'rb') as file:
            buf = file.read()
            hasher.update(buf)
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

    @staticmethod
    def get_payload(form):
        inputs = form.find_all('input')
        payload = {}
        for input_element in inputs:
            if input_element.has_attr('value'):
                payload[input_element['name']] = input_element['value']
        return payload

    @staticmethod
    def override_payload(payload, override):
        for k, v in override.items():
            payload[k] = v

    @staticmethod
    def decode(value, dictionary):
        rep = re.findall('\\[(.*?)\\]', value)
        for item in rep:
            if dictionary.get(item):
                value = value.replace("["+item+"]", dictionary[item])
        return value

    def check_json(self, filename):
        try:
            with open(filename) as file:
                is_logged_in = {}
                json_file = json.load(file)
                logins = json_file["login"]
                for login in logins:
                    try:
                        login_id = login["id"]
                        is_logged_in[login_id] = False
                        verify_ssl = True
                        page = None
                        payload = None

                        for step in login["steps"]:
                            if step["command"].lower() == 'verify_ssl':
                                if step["param"].lower() == 'true':
                                    verify_ssl = True
                                else:
                                    verify_ssl = False
                            elif step["command"].lower() == 'get':
                                page = self.get_soup(step["param"], verify=verify_ssl)
                            elif step["command"].lower() == 'post':
                                res = self.post(step["param"], payload, verify=verify_ssl)
                                page = BeautifulSoup(res.text, 'html.parser')
                            elif step["command"].lower() == 'select_form':
                                payload = self.get_payload(page.select_one(step["param"]))
                            elif step["command"].lower() == 'override_payload':
                                for payload_key, payload_value in step["param"].items():
                                    payload[self.decode(payload_key, payload)] = self.decode(payload_value, payload)

                        if login["verify_login"] in page.contents:
                            is_logged_in[login_id] = False
                        else:
                            is_logged_in[login_id] = True
                    except KeyError:
                        self.log("Missing key for login, skipping")
                        continue
                    except requests.exceptions.SSLError:
                        self.log("SSLError, stopping")
                        os._exit(-1)
                sites = json_file["sites"]
                for site in sites:
                    try:
                        site_id = site["id"]
                        if site.get("require"):
                            if not is_logged_in[site["requires"].strip()]:
                                self.log("Missing required login '" + site["requires"].strip() + "' for " + site_id)
                                continue
                        url = site["url"]
                        select_element = 'body'
                        if site.get("select_element"):
                            select_element = site["select_element"]
                        select_attrs = None
                        if site.get("select_attrs"):
                            select_attrs = site["select_attrs"]
                        remove_ids = None
                        if site.get("remove_ids"):
                            remove_ids = site["remove_ids"]
                        remove_classes = None
                        if site.get("remove_classes"):
                            remove_classes = site["remove_classes"]
                        verify = site["verify_ssl"]
                        if verify.lower() == 'true':
                            verify = True
                        else:
                            verify = False
                        self.track(site_id, url, select_element, select_attrs, remove_ids, remove_classes, verify)
                    except KeyError:
                        self.log("Missing key, skipping")
                        continue
                    except requests.exceptions.SSLError:
                        self.log("SSLError, stopping")
                        os._exit(-1)
        except FileNotFoundError:
            self.log("File Not Found: " + filename)
            os._exit(-1)
        except json.JSONDecodeError:
            self.log("Malformed JSON File " + filename)
            os._exit(-1)

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
            hasher = hashlib.md5()
            hasher.update(res.encode('utf-8'))
            new_hash = hasher.hexdigest()

            if site_id in self.hashes:
                if self.hashes[site_id] != new_hash:
                    self.log("'" + site_id + "' has changed")
                    self.hashes[site_id] = new_hash
                    self.write_track_file(site_id, res)
            else:
                self.hashes[site_id] = new_hash
                self.write_track_file(site_id, res)
        except requests.exceptions.RequestException:
            self.log("Request Error")
            os._exit(-1)


def tracker():
    return WebTracker()
