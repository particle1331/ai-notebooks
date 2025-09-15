import builtins
import os
import textwrap
import inspect

from typing import Any

from IPython.display import HTML, display, display_markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer


def hello():
    print("Hello from notebooks!")


def load_dotenv(verbose=False):
    with open(".env") as f:
        for line in f.readlines():
            k, v = line.split("=")
            os.environ[k] = v.strip().strip('"')
            if verbose:
                print(f"Loaded env variable: {k}")


def print(*args, wrap: bool = False, width: int = 80, **kwargs):
    new_args = []
    for arg in args:
        if wrap and isinstance(arg, str):
            new_args.append(textwrap.fill(arg, width=width))
        else:
            new_args.append(arg)
    builtins.print(*new_args, **kwargs)


def print_markdown(s: str):
    display_markdown(s, raw=True)


def display_python(code: str | Any):
    # Generate highlighted HTML
    code = inspect.getsource(code) if not isinstance(code, str) else code
    formatter = HtmlFormatter(style="colorful", cssclass="highlight")
    highlighted_code = highlight(code, PythonLexer(), formatter)

    # Get the CSS for the style
    css = formatter.get_style_defs(".highlight")

    # Display both CSS and code
    display(HTML(f"<style>{css}</style>"))
    display(HTML(highlighted_code))
