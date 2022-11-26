import os
import platform
import re
import hashlib
from typing import List, Tuple


def get_hash(text: bytes):
    hasher = hashlib.md5()
    hasher.update(text)
    return hasher.hexdigest()


def get_payload(form):
    inputs = form.find_all('input')
    payload = {}
    for input_element in inputs:
        if input_element.has_attr('value'):
            payload[input_element['name']] = input_element['value']
    return payload


def override_payload(payload, override):
    for k, v in override.items():
        payload[k] = v


def decode(value, dictionary):
    rep = re.findall('\\[(.*?)]', value)
    for item in rep:
        if dictionary.get(item):
            value = value.replace("[" + item + "]", dictionary[item])
    return value


html_start = """<!DOCTYPE html>
<html>
<head>
\t<title>Website Update</title>
\t<meta charset="utf-8">
\t<style>.container { border: 4px solid lightgrey; padding: .5em 1.5em; border-radius: 1em; margin: .6em 0; } \
h1 { text-align: center; margin: .4em; } hr { border-color: lightgrey; margin: 1em 0;} p { margin: .5em 0; } \
.added { color: green; } .removed { color: red; } .anchor { color: blue; }</style>
</head>
<body>
"""

html_end = """</body>
</html>"""

text_start = "Website Update"


def make_email_body(data: List[Tuple[str, str, str]]):
    global html_start
    global html_end

    email_text = ""
    email_text += text_start
    
    email_html = ""
    email_html += html_start

    for title, url, diff in data:
        email_text += f"\n\n{title} ({url})\n\n"
        email_text += diff
    
        email_html += "\t<div class=\"container\">\n"
        email_html += f"\t<h1>{title} (<a href=\"{url}\">link</a>)</h1>\n\t<hr/>\n"
        for line in diff.splitlines()[2:]:
            if line[0] == ' ':
                email_html += f"\t<p>&nbsp;{line}</p>\n"
            elif line[0] == '@':
                email_html += f"\t<p class=\"anchor\">{line}</p>\n"
            elif line[0] == '+':
                email_html += f"\t<p class=\"added\">{line}</p>\n"
            elif line[0] == '-':
                email_html += f"\t<p class=\"removed\">{line}</p>\n"
        email_html += "\t</div>\n"

    email_html += html_end

    return email_text, email_html
        

def notify(message: str):
    if platform.system() == "Linux":
        os.system(f"notify-send \"WebTracker\" \"{message}\"")
    elif platform.system() == "Darwin":
        os.system(f"osascript -e 'display notification \"{message}\" with title \"WebTracker\"'")
