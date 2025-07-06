from IPython.display import display, HTML
from IPython import get_ipython
from pathlib import Path

def get_latest_file(folder: str):
    p = Path(folder)
    fn = max(p.glob("**/*.cpp"), key=lambda f: f.stat().st_mtime)
    return fn.name.replace(".cpp", "")

def run(fn: str=None, comp: bool=True):
    fn = get_latest_file("./code") if fn is None else fn
    cmd = f"!./code/{fn}"
    if comp:
        cmd = f"!g++-15 ./code/{fn}.cpp -o ./code/{fn}\n" + cmd

    # run
    print((cmd + "\n").replace("!", "$ "))
    get_ipython().run_cell(cmd)
