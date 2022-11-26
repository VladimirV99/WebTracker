# Web Tracker

Web Tracker is a command line utility used for sending notifications when a webpage changes.
It supports filtering the webpage, selecting a specific part of a webpage to track, logging into websites and sending system notifications and emails.

## Requirements
- python 3
- beautifulsoup4

## Usage
```bash
python tracker.py -t [time] -f [file]
```
where `time` is the interval between checks in seconds and `file` is the path to the configuration file.
The syntax for the configuration file is specified under the [Configuration file section](#configuration-file).

When a website changes, a system notification is issued, subscribers are notified via email and the changes are saved to a log file.
Starting the script creates a new log file in the `logs` directory.
The latest version of each tracked website can be found in the `track` directory.

## Configuration file
The configuration file consists of 3 sections `login`, `sites` and `notify`.
Only the `sites` section is required, others are optional.

### `login` section
This section contains a list of login information.
If no site requires login, the section can be omitted.
Each item contains the following:
- `id` : string - Login id used by the `required` field in `sites` section
- `steps` : list - List of steps to perform to log in. Every step is an object with a `command` and a `param` field. Supported commands are:
  - `verify_ssl` - Should use secure connection. Default: `true`
  - `get` - Issue a GET request to url in `param`
  - `select_form` - Select the login form using a css selector  in `param`
  - `override_payload` - Set form data as in `param` dict
  - `post` - Issue a POST request with the payload obtained by `select_form` to url in `param`
- `verify_login` : string - Optional. String found in the webpage if the login was unsuccessful. If not provided, the login is assumed to have succeeded

For most use cases required steps in order are: `get`, `select_form`, `override_payload` and `post`.

### `sites` section
This section contains the list of sites to track.
Each item contains the following:
- `id` : string - Site id. Printed to user when a change occurs
- `requires` : string - Optional. ID of login entry
- `verify_ssl` : bool - Should use secure connection. Default: `true`
- `select_element` : string - Select part of webpage to track by tag name
- `select_attrs` : dict - Select part of webpage to track by attributes
- `remove_ids` : list[string] - List of element remove specified by their ids
- `remove_classes` : list[string] - List of element remove specified by their classes
- `remove_attrs` : list[dict] - List of element remove specified by their attributes
- `url` : string - Webpage url

### `notify` section
This section is optional. If any of the following are missing, email notifications will be disabled
- `sender` : dict - Sender information. Contains the following fields:
	- `smtp_host` : string - Host url of SMTP server
	- `smtp_port` : int - Host port of SMTP server
	- `email` : string - Senders email address
	- `password` : string - Senders password
- `recipients` : list[string] - Recipient emails

### Example configuration file
```json
{
    "notify": {
        "sender": {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "email": "example@gmail.com",
            "password": "password"
        },
        "recipients": [ "user@gmail.com" ]
    },
    "login": [
        {
            "id": "example_login",
            "steps": [
                { "command": "verify_ssl", "param": false },
                { "command": "get", "param": "https://www.example.com/login.php"},
                { "command": "select_form", "param": "form" },
                { "command": "override_payload", "param": {
                        "username": "admin",
                        "password": "password"
                    }
                },
                { "command": "post", "param": "https://www.example.com/login.php" }
            ],
            "verify_login": "Login Failed"
        }
    ],
    "sites": [
        {
            "id": "example",
            "requires": "example_login",
            "verify_ssl": true,
            "select_element": "div",
            "select_attrs": {
                "attr": "value"
            },
            "remove_ids": [ "id_to_remove" ],
            "remove_classes": [ "class_to_remove" ],
            "remove_attrs": [
                { "attr": "value" }
            ],
            "url": "https://www.example.com/dashboard.php"
        }
    ]
}
```
