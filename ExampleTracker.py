import requests
import time
import webtrack
import utils

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


def start_tracking():
    check_time = 15 * 60  # 15 Minutes
    tracker = webtrack.WebTracker()
    tracker.start_session()

    while True:
        example_site = tracker.get_soup('https://www.example.com/login.php')
        example_payload = utils.get_payload(example_site.find('form'))
        utils.override_payload(example_payload, {'username': 'admin', 'password': 'pass'})
        tracker.post('https://www.example.com/login.php', example_payload)

        status, diff = tracker.track(site_id='example', url='https://www.example.com/dashboard.php')
        if not status:
            utils.notify("Tracker crashed")
            break

        time.sleep(check_time)


def main():
    try:
        start_tracking()
    except KeyboardInterrupt:
        print("\nStopping tracker")
        exit(0)


main()
