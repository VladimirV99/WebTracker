import os


def main():
    if os.path.exists("log"):
        for file in os.listdir("log"):
            if file.endswith(".txt"):
                os.remove("log/" + file)


main()
