import os


def hello():
    print("Hello from notebooks!")


def load_dotenv(verbose=False):
    with open(".env") as f:
        for line in f.readlines():
            k, v = line.split("=")
            os.environ[k] = v.strip().strip('"')
            if verbose:
                print(f"Loaded env variable: {k}")
