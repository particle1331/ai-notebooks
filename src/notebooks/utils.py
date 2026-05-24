import os
import sys
import rich
import inspect
import pathlib

import torch
import random
import numpy as np

from typing import Any

from IPython.display import HTML, display, display_markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

from notebooks.constants import ROOT_PATH, DATA_PATH, ARTIFACTS_PATH

def init():
    DATA_PATH.mkdir(exist_ok=True)
    ARTIFACTS_PATH.mkdir(exist_ok=True)


def pprint(x, wrap=False, width=80, expand_all=False, indent_guides=True, **kwargs):
    P = rich.pretty.Pretty
    T = rich.theme.Theme({"repr.indent": "dim grey50",})
    console = rich.console.Console(theme=T)
    if wrap and isinstance(x, str):
        x = "\n".join([x[i:i+width] for i in range(0, len(x), width)])
        print(x, **kwargs)
    else:
        p = P(x, expand_all=expand_all, indent_guides=indent_guides, **kwargs)
        console.print(p, soft_wrap=not wrap, width=width)


def hello():
    print("Hello from notebooks!")


def load_dotenv(path=None, verbose=False):
    path = path or ".env"
    with open(path) as f:
        for line in f.readlines():
            k, v = line.split("=")
            os.environ[k] = v.strip().strip('"')
            if verbose:
                print(f"Loaded env variable: {k}")


def display_python(code: str | list[str] | Any):
    get_source = lambda c: inspect.getsource(c) if not isinstance(c, str) else c
    if isinstance(code, list):
        code = "\n\n".join([get_source(c) for c in code])
    else:
        code = get_source(code)

    formatter = HtmlFormatter(style="colorful", cssclass="highlight")
    highlighted_code = highlight(code, PythonLexer(), formatter)

    # Get the CSS for the style
    css = formatter.get_style_defs(".highlight")

    # Display both CSS and code
    display(HTML(f"<style>{css}</style>"))
    display(HTML(highlighted_code))



def get_device(): 
    return (
        torch.device("cuda:0") if torch.cuda.is_available() else (
            torch.device("mps") if torch.mps.is_available() else 
                torch.device("cpu")
        )
    )


class eval_context:
    """Context manager to set model to eval mode."""
    def __init__(self, model):
        self.model = model
        self.state = model.training

    def __enter__(self):
        self.model.eval()

    def __exit__(self, exc_type, exc_value, traceback):
        self.model.train(self.state)


def set_seed(value=42, deterministic=False):
    """Set the seed for reproducibility. 
    
    WARNING: Setting deterministic=True may result in decreased performance. 
    e.g. disabling benchmarking causes cuDNN to deterministically select an 
    algorithm, possibly at the cost of reduced performance.
    """

    random.seed(value)
    np.random.seed(value)
    torch.manual_seed(value)
    
    if deterministic:
        torch.backends.cudnn.benchmark = False
        torch.use_deterministic_algorithms(True)
    else:
        torch.backends.cudnn.benchmark = True
        torch.use_deterministic_algorithms(False)

    print(f"seed: {value}  deterministic: {deterministic}")


init()
