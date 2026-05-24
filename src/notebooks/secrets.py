"""
secrets.py — Secure API key retrieval for ai-notebooks.

On macOS, keys are fetched from the macOS Keychain via the `keyring` library.
On other platforms, keys are loaded from a `.env` file in the current working
directory (or a path you provide).

macOS — store a key once via CLI:
    python -m notebooks.secrets set OPENAI_API_KEY sk-...
    # or directly with the security CLI:
    security add-generic-password -a OPENAI_API_KEY -s ai-notebooks -w "sk-..."

Other platforms — create a .env file:
    OPENAI_API_KEY=sk-...
    GROQ_API_KEY=gsk_...

Usage in notebooks / code:
    from notebooks.secrets import get_secret
    api_key = get_secret("OPENAI_API_KEY")
"""

import os
import sys
import pathlib

from notebooks.constants import ROOT_PATH

# Service name used as the Keychain namespace on macOS.
_KEYCHAIN_SERVICE = "ai-notebooks"
_IS_MACOS = sys.platform == "darwin"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_from_keychain(key: str) -> str | None:
    """Return the secret stored in macOS Keychain, or None if not found."""
    try:
        import keyring  # noqa: PLC0415
        return keyring.get_password(_KEYCHAIN_SERVICE, key)
    except Exception:
        return None


def _load_dotenv(env_path: pathlib.Path) -> dict[str, str]:
    """Parse a .env file and return a {key: value} dict (no shell quoting)."""
    pairs: dict[str, str] = {}
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        pairs[k.strip()] = v.strip().strip('"').strip("'")
    return pairs


def _get_from_dotenv(key: str, env_path: pathlib.Path) -> str | None:
    """Return the value of *key* from a .env file, or None if absent."""
    if not env_path.exists():
        return None
    return _load_dotenv(env_path).get(key)


def _parse_keychain_dump(output: str) -> list[str]:
    """Extract account names for our service from `security dump-keychain` output."""
    entries: list[str] = []
    current: list[str] = []

    def process_block(block: list[str]) -> None:
        text = "\n".join(block)
        if f'"svce"<blob>="{_KEYCHAIN_SERVICE}"' not in text:
            return
        for line in block:
            line = line.strip()
            if line.startswith('"acct"') and '="' in line:
                entries.append(line.split('="', 1)[1].rstrip('"'))

    for line in output.splitlines():
        if line.startswith("keychain:") and current:
            process_block(current)
            current = []
        current.append(line)

    if current:
        process_block(current)

    return entries


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_secret(
    key: str,
    *,
    env_file: str | pathlib.Path = ROOT_PATH / ".env",
    raise_on_missing: bool = True,
) -> str | None:
    """Retrieve an API key / secret by name.

    Resolution order
    ----------------
    1. Environment variable `key` (already exported in the shell).
    2. macOS Keychain (macOS only) under service `"ai-notebooks"`.
    3. `.env` file (all platforms) at *env_file* path.

    Parameters
    ----------
    key:
        The secret name, e.g. `"OPENAI_API_KEY"`.
    env_file:
        Path to the `.env` file used as fallback on non-macOS systems
        (and as a secondary fallback on macOS). Defaults to `.env` at the
        project root.
    raise_on_missing:
        When `True` (default) raise `RuntimeError` if the secret cannot be
        found anywhere.  When `False` return `None` instead.

    Returns
    -------
    str | None
        The secret value, or `None` if *raise_on_missing* is `False` and
        the secret was not found.
    """
    env_path = pathlib.Path(env_file).expanduser()

    # 1. Environment variable (highest priority, works everywhere).
    value = os.environ.get(key)
    if value:
        return value

    if _IS_MACOS:
        # 2a. macOS Keychain.
        value = _get_from_keychain(key)
        if value:
            return value

        # 2b. .env fallback (useful during initial setup or CI).
        value = _get_from_dotenv(key, env_path)
        if value:
            return value

        if raise_on_missing:
            raise RuntimeError(
                f"Secret '{key}' not found.\n\n"
                "Store it in the macOS Keychain with:\n"
                f"   python -m notebooks.secrets set {key} <value>\n"
                "or:\n"
                f"   security add-generic-password -a {key} -s {_KEYCHAIN_SERVICE} -w '<value>'\n\n"
                f"Alternatively, add it to '{env_path.resolve()}' as:\n"
                f"   {key}=<value>"
            )
    else:
        # 2. .env file on non-macOS platforms.
        value = _get_from_dotenv(key, env_path)
        if value:
            return value

        if raise_on_missing:
            raise RuntimeError(
                f"Secret '{key}' not found.\n\n"
                f"This platform ({sys.platform}) does not use the macOS Keychain.\n"
                f"Please provide a .env file at:\n"
                f"   {env_path.resolve()}\n\n"
                "with contents like:\n"
                f"   {key}=<value>"
            )

    return None


def set_secret(key: str, value: str) -> None:
    """Store *key* / *value* in the macOS Keychain (macOS only).

    Raises `RuntimeError` on non-macOS systems.
    """
    if not _IS_MACOS:
        raise RuntimeError(
            f"set_secret() is only supported on macOS (current platform: {sys.platform}).\n"
            "On other platforms, add the key to your .env file manually."
        )
    import keyring  # noqa: PLC0415
    keyring.set_password(_KEYCHAIN_SERVICE, key, value)
    print(f"✓ Stored '{key}' in macOS Keychain under service '{_KEYCHAIN_SERVICE}'.")


def delete_secret(key: str) -> None:
    """Delete *key* from the macOS Keychain (macOS only).

    Raises `RuntimeError` on non-macOS systems.
    """
    if not _IS_MACOS:
        raise RuntimeError(
            f"delete_secret() is only supported on macOS (current platform: {sys.platform})."
        )
    import keyring  # noqa: PLC0415
    keyring.delete_password(_KEYCHAIN_SERVICE, key)
    print(f"✓ Deleted '{key}' from macOS Keychain (service '{_KEYCHAIN_SERVICE}').")


def list_secrets() -> None:
    """Print all keys stored under the ai-notebooks service (macOS only)."""
    if not _IS_MACOS:
        raise RuntimeError(
            f"list_secrets() is only supported on macOS (current platform: {sys.platform})."
        )

    import subprocess  # noqa: PLC0415

    result = subprocess.run(
        ["security", "dump-keychain"],
        capture_output=True,
        text=True,
    )
    entries = _parse_keychain_dump(result.stdout)

    if entries:
        print(f"Keys stored under service '{_KEYCHAIN_SERVICE}':")
        for e in sorted(set(entries)):
            print(f"  • {e}")
    else:
        print(f"No keys found under service '{_KEYCHAIN_SERVICE}'.")
