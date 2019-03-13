import requests
import threading
import time
import webtrack

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

check_time = 15*60  # 15 Minutes
tracker = webtrack.tracker()


def start_tracking():
    tracker.start_session()

    while True:
        example_site = tracker.get_soup('https://www.example.com/login.php', verify=False)
        example_payload = tracker.get_payload(example_site.find('form'))
        tracker.override_payload(example_payload, {'username': 'admin', 'password': 'pass'})
        tracker.post('https://www.example.com/login.php', example_payload, verify=False)

        tracker.track(site_id='example', url='https://www.example.com/dashboard.php', verify=False)

        time.sleep(check_time)


def main():
    t = threading.Thread(target=start_tracking, args=())
    t.setDaemon(True)
    t.start()

    while True:
        try:
            command = input()
            if command == "exit":
                exit(0)
        except KeyboardInterrupt:
            print("\nStopping tracker")
            exit(0)


main()
