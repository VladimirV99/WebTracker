import re
import mailer


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
    rep = re.findall('\\[(.*?)\\]', value)
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
.added { color: green; } .removed { color: red; }</style>
</head>
<body>
"""

html_end = """</body>
</html>"""


def make_html(data):
    global html_start
    global html_end

    html = ""
    html += html_start

    for title, text in data.items():
        html += "\t<div class=\"container\">\n"
        html += "\t<h1>" + title + "</h1>\n\t<hr/>\n"
        for line in text.splitlines()[2:]:
            if line[0] == ' ':
                html += "\t<p>&nbsp;" + line + "</p>\n"
            elif line[0] == '+':
                html += "\t<p class=\"added\">" + line + "</p>\n"
            elif line[0] == '-':
                html += "\t<p class=\"removed\">" + line + "</p>\n"
        html += "\t</div>\n"

    html += html_end

    return html


def notify(mails, data):
    if len(mails) > 0:
        html = make_html(data)
        mailer.send_mails(mails, html)
