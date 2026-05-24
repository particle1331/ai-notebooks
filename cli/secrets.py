"""
cli/secrets.py — Manage API keys in the macOS Keychain.

Usage via Makefile:
    make secrets list
    make secrets set     OPENAI_API_KEY sk-...
    make secrets get     OPENAI_API_KEY
    make secrets delete  OPENAI_API_KEY
    make secrets test    openai

Usage directly:
    uv run cli/secrets.py <command> [args]
"""

import typer                                        # noqa: E402
from openai import OpenAI, AuthenticationError      # noqa: E402
from notebooks.secrets import (                     # noqa: E402  # type: ignore[import]
    get_secret,
    set_secret,
    delete_secret,
    list_secrets,
)


app = typer.Typer(help="Manage API keys in the macOS Keychain.")

@app.command()
def set(key: str, value: str) -> None:
    """Store a key in the Keychain."""
    set_secret(key, value)

@app.command()
def get(key: str) -> None:
    """Retrieve and print a key value."""
    typer.echo(get_secret(key))

@app.command()
def delete(key: str) -> None:
    """Delete a key from the Keychain."""
    delete_secret(key)

@app.command(name="list")
def list_() -> None:
    """List all stored key names."""
    list_secrets()

@app.command()
def test(service: str = typer.Argument("openai")) -> None:
    """Test a stored API key."""
    if service != "openai":
        typer.echo(f"Unknown service: {service}")
        raise typer.Exit(code=1)
    key = get_secret("OPENAI_API_KEY")
    try:
        OpenAI(api_key=key).models.list()
        typer.echo("OPENAI_API_KEY is VALID ✔")
    except AuthenticationError:
        typer.echo("OPENAI_API_KEY is INVALID ✖  (authentication failed)")
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"OPENAI_API_KEY check FAILED ✖  ({e})")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
