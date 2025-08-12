.PHONY: docs

docs:
	quarto preview

requirements:
	uv pip compile pyproject.toml > requirements.txt
