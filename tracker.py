import argparse
import requests
import sys
import time
import os
import webtrack
import utils

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--time', type=int, default=15 * 60, help='Check interval in seconds')
    parser.add_argument('-f', '--file', required=True, help='Input file')
    parser.add_argument('--log-path', default="logs", help='Path to the log files')
    parser.add_argument('--track-path', default="track", help='Path to the track files')
    parser.add_argument('--disable-email', action='store_true', help='Disable sending email notifications')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    return parser.parse_args()


def start_tracking(file: str, check_time: int, log_path: str, track_path: str, disable_email: bool):
    tracker = webtrack.WebTracker(log_path=log_path, track_path=track_path, email_notify=not disable_email)
    tracker.start_session()
    while True:
        if not tracker.check_json(file):
            utils.notify("Tracker crashed")
            break
        time.sleep(check_time)


def main():
    args = parse_args()
    check_time = args.time
    log_path = args.log_path
    track_path = args.track_path
    disable_email = args.disable_email

    if not os.path.exists(args.file) or os.path.isdir(args.file):
        print(f"Invalid input file '{args.file}'")
        return

    if check_time < 60:
        print("Check interval too small. Changing to 1 minute")
        check_time = 60

    try:
        start_tracking(args.file, check_time, log_path, track_path, disable_email)
    except KeyboardInterrupt:
        print("\nStopping tracker")
        exit(0)

if __name__ == '__main__':
    main()
