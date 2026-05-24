.PHONY: docs uv venv requirements secrets

docs:
	quarto preview

uv:
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	else \
		echo "uv already installed."; \
	fi

requirements: uv
	uv pip compile pyproject.toml > requirements.txt

venv: uv
	uv venv --python 3.13
	uv sync

secrets:
	uv run cli/secrets.py $(filter-out $@,$(MAKECMDGOALS))

# Absorb any extra words passed after 'make secrets <cmd>' so make doesn't
# treat them as targets.
%:
	@:
