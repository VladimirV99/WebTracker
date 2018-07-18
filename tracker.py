import argparse
import requests
import sys
import threading
import time
import webtrack

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

tracker = webtrack.tracker()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--time', nargs=1, type=int, default=15*60, help='Check interval in seconds')
    parser.add_argument('-f', '--file', nargs=1, required=True, help='Input file')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    return parser.parse_args()


def start_tracking():
    args = parse_args()
    check_time = args.time
    tracker.start_session()
    while True:
        tracker.check_json(args.file[0])
        time.sleep(check_time)


def main():
    t = threading.Thread(target=start_tracking, args=())
    t.setDaemon(True)
    t.start()

    while True:
        try:
            command = input()
            if command.lower() == "exit" or command.lower() == "stop" or command.lower() == "quit":
                exit(0)
        except KeyboardInterrupt:
            print("\nStopping tracker")
            exit(0)


main()
