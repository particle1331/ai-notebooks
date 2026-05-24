"""
cli/secrets.py — Manage API keys in the macOS Keychain.

Usage via Makefile:
    make secrets set   KEY=OPENAI_API_KEY VALUE=sk-...
    make secrets get   KEY=OPENAI_API_KEY
    make secrets delete KEY=OPENAI_API_KEY
    make secrets list
    make secrets test  SERVICE=openai

Usage directly:
    uv run cli/secrets.py <command> [args]
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "src"))

import argparse  # noqa: E402
from openai import OpenAI, AuthenticationError  # noqa: E402
from notebooks.secrets import (  # noqa: E402  # type: ignore[import]
    get_secret,
    set_secret,
    delete_secret,
    list_secrets,
)


def test_openai_key(api_key: str | None = None) -> bool:
    """Test whether an OpenAI API key is valid by listing models."""
    key = api_key or get_secret("OPENAI_API_KEY")
    try:
        OpenAI(api_key=key).models.list()
        print("OPENAI_API_KEY is VALID ✔")
        return True
    except AuthenticationError:
        print("OPENAI_API_KEY is INVALID ✖  (authentication failed)")
        return False
    except Exception as e:
        print(f"OPENAI_API_KEY check FAILED ✖  ({e})")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="secrets",
        description="Manage API keys in the macOS Keychain.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set", help="Store a key in the Keychain.")
    p_set.add_argument("key", help="Secret name, e.g. OPENAI_API_KEY")
    p_set.add_argument("value", help="Secret value")

    p_del = sub.add_parser("delete", help="Delete a key from the Keychain.")
    p_del.add_argument("key", help="Secret name to delete")

    p_get = sub.add_parser("get", help="Retrieve and print a key value.")
    p_get.add_argument("key", help="Secret name to retrieve")

    sub.add_parser("list", help="List all stored key names.")

    p_test = sub.add_parser("test", help="Test a stored API key.")
    p_test.add_argument(
        "service",
        choices=["openai"],
        help="Service to test (currently: openai)",
    )

    args = parser.parse_args()

    if args.command == "set":
        set_secret(args.key, args.value)
    elif args.command == "delete":
        delete_secret(args.key)
    elif args.command == "get":
        print(get_secret(args.key))
    elif args.command == "list":
        list_secrets()
    elif args.command == "test":
        if args.service == "openai":
            test_openai_key()


if __name__ == "__main__":
    main()
