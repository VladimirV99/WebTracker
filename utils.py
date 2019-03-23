import re


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
