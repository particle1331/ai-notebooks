import shlex
import argparse
import subprocess
from IPython.core.magic import register_cell_magic

def parse_args(line):
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs="?", default="tmp.cpp")
    parser.add_argument("--run", type=lambda x: x.lower() != "false", default=True)
    parser.add_argument("--exitcode", type=lambda x: x.lower() == "true", default=False)
    args = parser.parse_args(shlex.split(line))
    return args

@register_cell_magic
def runcpp(line, cell):
    args = parse_args(line)
    with open(f"./code/{args.filename}", "w") as file:
        file.write(cell)

    # compile and run
    fn = args.filename.split(".")[0]
    run = f"\n./code/{fn}" * int(args.run)
    cmd = f"g++-15 ./code/{fn}.cpp -o ./code/{fn}" + run

    print(cmd + "\n")
    ret = subprocess.run(cmd, shell=True)
    if args.exitcode:
        print(ret.returncode)
