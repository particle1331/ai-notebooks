"""Base classes for the tool system.

Defines the Tool ABC, ToolResult, ToolKind, FileDiff, ToolInvocation,
and ToolConfirmation — the primitives that every tool implementation uses.
"""

from __future__ import annotations

import abc
import difflib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError
from pydantic.json_schema import model_json_schema

from notebooks.agent.config import Config


class ToolKind(str, Enum):
    """Categorizes tools for approval logic and UI styling."""

    READ = "read"
    WRITE = "write"
    SHELL = "shell"
    NETWORK = "network"
    MEMORY = "memory"


@dataclass
class FileDiff:
    """Captures the before/after state of a file edit."""

    path: Path
    old_content: str
    new_content: str
    is_new_file: bool = False
    is_deletion: bool = False

    def to_diff(self) -> str:
        old_lines = self.old_content.splitlines(keepends=True)
        new_lines = self.new_content.splitlines(keepends=True)

        if old_lines and not old_lines[-1].endswith("\n"):
            old_lines[-1] += "\n"
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"

        old_name = "/dev/null" if self.is_new_file else str(self.path)
        new_name = "/dev/null" if self.is_deletion else str(self.path)

        return "".join(
            difflib.unified_diff(old_lines, new_lines, fromfile=old_name, tofile=new_name)
        )


@dataclass
class ToolResult:
    """The result of executing a tool."""

    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    truncated: bool = False
    diff: FileDiff | None = None
    exit_code: int | None = None

    @classmethod
    def error_result(cls, error: str, output: str = "", **kwargs: Any) -> ToolResult:
        return cls(success=False, output=output, error=error, **kwargs)

    @classmethod
    def success_result(cls, output: str, **kwargs: Any) -> ToolResult:
        return cls(success=True, output=output, error=None, **kwargs)

    def to_model_output(self) -> str:
        """Format for inclusion in the LLM conversation as a tool result."""
        if self.success:
            return self.output
        return f"Error: {self.error}\n\nOutput:\n{self.output}"


@dataclass
class ToolInvocation:
    """Parameters passed to a tool's execute method."""

    params: dict[str, Any]
    cwd: Path


@dataclass
class ToolConfirmation:
    """Data needed for the approval dialog."""

    tool_name: str
    params: dict[str, Any]
    description: str
    diff: FileDiff | None = None
    affected_paths: list[Path] = field(default_factory=list)
    command: str | None = None
    is_dangerous: bool = False


class Tool(abc.ABC):
    """Abstract base class for all tools.

    Subclasses must set the following class attributes:
      - ``name``          – unique tool identifier
      - ``description``   – one-line tool summary for the LLM
      - ``kind``          – :class:`ToolKind` category
      - ``schema``        – a Pydantic ``BaseModel`` subclass **or** a dict

    And implement :meth:`execute`.
    """

    name: str = "base_tool"
    description: str = "Base tool"
    kind: ToolKind = ToolKind.READ

    def __init__(self, config: Config) -> None:
        self.config = config

    schema: type[BaseModel] | dict[str, Any]

    @abc.abstractmethod
    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        pass

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """Validate parameters against the schema."""
        schema = self.schema
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            try:
                schema(**params)
            except ValidationError as e:
                errors = []
                for err in e.errors():
                    loc = ".".join(str(x) for x in err.get("loc", []))
                    msg = err.get("msg", "Validation error")
                    errors.append(f"Parameter '{loc}': {msg}")
                return errors
            except Exception as e:
                return [str(e)]
        return []

    def is_mutating(self, params: dict[str, Any]) -> bool:
        """Whether this tool modifies state (drives approval logic)."""
        return self.kind in {ToolKind.WRITE, ToolKind.SHELL, ToolKind.NETWORK, ToolKind.MEMORY}

    async def get_confirmation(self, invocation: ToolInvocation) -> ToolConfirmation | None:
        """Return confirmation data if this invocation needs approval."""
        if not self.is_mutating(invocation.params):
            return None
        return ToolConfirmation(
            tool_name=self.name,
            params=invocation.params,
            description=f"Execute {self.name}",
        )

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to the format expected by OpenAI function calling."""
        schema = self.schema

        if isinstance(schema, type) and issubclass(schema, BaseModel):
            json_schema = model_json_schema(schema, mode="serialization")
            return {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": json_schema.get("properties", {}),
                    "required": json_schema.get("required", []),
                },
            }

        if isinstance(schema, dict):
            result: dict[str, Any] = {
                "name": self.name,
                "description": self.description,
            }
            if "parameters" in schema:
                result["parameters"] = schema["parameters"]
            else:
                result["parameters"] = schema
            return result

        raise ValueError(f"Invalid schema type for tool {self.name}: {type(schema)}")
