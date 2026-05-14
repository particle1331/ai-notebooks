"""Conversation state for a single agent session.

Wires together the LLM client, tool registry, and message history.
The session is a data holder with convenience methods — it does NOT
drive the agentic loop (that responsibility belongs to the Agent class).

Sessions can be serialized to / from JSON for persistence::

    data = session.to_dict()
    Session.from_dict(data, config)   # restore from a saved dict

The default save directory is ``~/.cda/sessions/``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from notebooks.agent.client import LLMClient
from notebooks.agent.config import Config
from notebooks.agent.events import TokenUsage, ToolResultMessage
from notebooks.agent.prompts import build_system_prompt
from notebooks.agent.tools.registry import ToolRegistry, create_default_registry

SESSIONS_DIR = Path.home() / ".cda" / "sessions"


class Session:
    """Manages conversation state for a single agent session.

    Parameters
    ----------
    config : Config
        Agent configuration (model settings, working directory, etc.).
    client : LLMClient | None
        LLM client for chat completions.  A default is created from
        *config* when ``None``.
    registry : ToolRegistry | None
        Tool registry.  The default builtin registry is created from
        *config* when ``None``.
    """

    def __init__(
        self,
        config: Config,
        client: LLMClient | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        self.config = config
        self.client = client if client is not None else LLMClient(config)
        self.registry = (
            registry if registry is not None else create_default_registry(config)
        )
        self._system_prompt = build_system_prompt(config, self.registry.get_tools())
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt},
        ]
        self.total_usage: TokenUsage = TokenUsage()
        self.turn_count: int = 0

    # ------------------------------------------------------------------ #
    #  Message helpers                                                     #
    # ------------------------------------------------------------------ #

    def add_user_message(self, content: str) -> None:
        """Append a user message to the conversation history."""
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(
        self,
        content: str,
        tool_calls: list[dict] | None = None,
    ) -> None:
        """Append an assistant message, optionally with tool calls.

        Parameters
        ----------
        content : str
            The text content of the assistant reply.
        tool_calls : list[dict] | None
            If provided, each dict should contain ``id``, ``name``, and
            ``arguments`` (a dict).  They are formatted into the OpenAI
            function-calling message structure.
        """
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls is not None:
            message["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": (
                            json.dumps(tc["arguments"])
                            if isinstance(tc["arguments"], dict)
                            else tc["arguments"]
                        ),
                    },
                }
                for tc in tool_calls
            ]
        self.messages.append(message)

    def add_tool_result(self, tool_result: ToolResultMessage) -> None:
        """Append a tool result message to the conversation history."""
        self.messages.append(tool_result.to_openai_message())

    # ------------------------------------------------------------------ #
    #  Accessors                                                           #
    # ------------------------------------------------------------------ #

    def get_messages(self) -> list[dict[str, Any]]:
        """Return the full message list."""
        return self.messages

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Return tool schemas for the current registry."""
        return self.registry.get_schemas()

    @property
    def system_prompt(self) -> str:
        """Return the current system prompt (first message content)."""
        return self.messages[0]["content"]

    # ------------------------------------------------------------------ #
    #  Tracking                                                            #
    # ------------------------------------------------------------------ #

    def track_usage(self, usage: TokenUsage) -> None:
        """Accumulate token usage from a single LLM call."""
        self.total_usage = self.total_usage + usage

    # ------------------------------------------------------------------ #
    #  Reset                                                               #
    # ------------------------------------------------------------------ #

    def reset(self) -> None:
        """Clear conversation back to the initial system prompt."""
        self.messages = [
            {"role": "system", "content": self._system_prompt},
        ]
        self.turn_count = 0
        self.total_usage = TokenUsage()

    # ------------------------------------------------------------------ #
    #  Persistence                                                         #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict[str, Any]:
        """Serialize session state to a JSON-compatible dict.

        The serialized form stores the full message history and token usage.
        Config is *not* stored — it must be provided again when calling
        :meth:`from_dict`.
        """
        return {
            "version": 1,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "turn_count": self.turn_count,
            "total_usage": {
                "prompt_tokens": self.total_usage.prompt_tokens,
                "completion_tokens": self.total_usage.completion_tokens,
                "total_tokens": self.total_usage.total_tokens,
                "cached_tokens": self.total_usage.cached_tokens,
            },
            "messages": self.messages,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        config: Config,
        client: LLMClient | None = None,
        registry: ToolRegistry | None = None,
    ) -> Session:
        """Restore a session from a previously serialized dict.

        Parameters
        ----------
        data:
            The dict returned by :meth:`to_dict`.
        config:
            Configuration for the restored session (creates a new
            ``LLMClient`` and ``ToolRegistry`` if *client*/*registry* are
            ``None``).
        client / registry:
            Optional pre-built instances to reuse.
        """
        session = cls(config, client=client, registry=registry)
        session.messages = data["messages"]
        session.turn_count = data.get("turn_count", 0)
        usage = data.get("total_usage", {})
        session.total_usage = TokenUsage(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            cached_tokens=usage.get("cached_tokens", 0),
        )
        return session

    def save(self, name: str, directory: Path = SESSIONS_DIR) -> Path:
        """Persist this session to *directory*/<name>.json.

        Parameters
        ----------
        name:
            Filename stem (no extension).  Spaces are replaced with
            underscores.
        directory:
            Directory to write into (created if missing).

        Returns
        -------
        Path
            The path of the written file.
        """
        directory.mkdir(parents=True, exist_ok=True)
        safe_name = name.replace(" ", "_")
        path = directory / f"{safe_name}.json"
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(
        cls,
        name: str,
        config: Config,
        directory: Path = SESSIONS_DIR,
        client: LLMClient | None = None,
        registry: ToolRegistry | None = None,
    ) -> Session:
        """Load a previously saved session from *directory*/<name>.json.

        Parameters
        ----------
        name:
            Filename stem (without .json extension).
        config:
            Configuration to wire into the restored session.
        directory:
            Directory to load from (default: ``~/.cda/sessions/``).
        client / registry:
            Optional pre-built instances.

        Raises
        ------
        FileNotFoundError
            If the session file does not exist.
        """
        safe_name = name.replace(" ", "_")
        path = directory / f"{safe_name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Session not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data, config, client=client, registry=registry)

    @staticmethod
    def list_saved(directory: Path = SESSIONS_DIR) -> list[str]:
        """Return a sorted list of saved session names in *directory*."""
        if not directory.exists():
            return []
        return sorted(p.stem for p in directory.glob("*.json"))
