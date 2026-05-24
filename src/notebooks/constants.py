"""_paths.py — Project-wide path constants."""

import pathlib

ROOT_PATH = pathlib.Path(__file__).parents[2]
DATA_PATH = ROOT_PATH / "data"
ARTIFACTS_PATH = ROOT_PATH / "artifacts"
