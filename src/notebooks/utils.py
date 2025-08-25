import os
import builtins
import textwrap


def hello():
    print("Hello from notebooks!")


def load_dotenv(verbose=False):
    with open(".env") as f:
        for line in f.readlines():
            k, v = line.split("=")
            os.environ[k] = v.strip().strip('"')
            if verbose:
                print(f"Loaded env variable: {k}")


def print(*args, wrap: bool=False, width: int=80, **kwargs):
    new_args = []
    for arg in args:
        if wrap and isinstance(arg, str):
            new_args.append(textwrap.fill(arg, width=width))
        else:
            new_args.append(arg)
    builtins.print(*new_args, **kwargs)
