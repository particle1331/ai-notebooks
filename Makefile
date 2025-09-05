.PHONY: docs uv venv requirements

docs:
	quarto preview

uv:
	pip install --upgrade pip
	pip install uv

requirements: uv
	uv pip compile pyproject.toml > requirements.txt

venv: uv
	uv venv --python 3.13
	uv sync

diff: # args="cf6450c 3139d8f", or args=cf6450c
	uv run python -m scripts.diff $(args)
