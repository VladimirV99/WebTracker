import os


def main():
    log_path = "logs"

    if os.path.exists(log_path):
        for file in os.listdir(log_path):
            if file.endswith(".txt"):
                os.remove(os.path.join(log_path, file))


main()
