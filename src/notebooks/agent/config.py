"""Agent configuration using Pydantic models.

Provides Config, ModelConfig, and ApprovalPolicy for the coding agent.
All secrets come from environment variables — never hardcoded.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from notebooks.agent.tools.mcp_bridge import MCPServerConfig


class ModelConfig(BaseModel):
    """LLM model configuration."""

    name: str = "anthropic/claude-sonnet-4"
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    context_window: int = 200_000


class ShellEnvironmentPolicy(BaseModel):
    """Controls which env vars are visible to shell tool execution."""

    ignore_default_excludes: bool = False
    exclude_patterns: list[str] = Field(
        default_factory=lambda: ["*KEY*", "*TOKEN*", "*SECRET*"]
    )
    set_vars: dict[str, str] = Field(default_factory=dict)


class ApprovalPolicy(str, Enum):
    """How the agent handles approval for mutating operations."""

    ON_REQUEST = "on-request"
    AUTO = "auto"
    NEVER = "never"
    YOLO = "yolo"


class Config(BaseModel):
    """Top-level agent configuration.

    API credentials are read from environment variables:
      - OPENROUTER_API_KEY  (or API_KEY as fallback)
      - OPENROUTER_BASE_URL (default: https://openrouter.ai/api/v1)
    """

    model: ModelConfig = Field(default_factory=ModelConfig)
    cwd: Path = Field(default_factory=Path.cwd)
    shell_environment: ShellEnvironmentPolicy = Field(
        default_factory=ShellEnvironmentPolicy
    )
    approval: ApprovalPolicy = ApprovalPolicy.ON_REQUEST
    max_turns: int = 100

    allowed_tools: list[str] | None = Field(
        None,
        description="If set, only these tools will be available to the agent",
    )

    mcp_servers: list[Any] = Field(
        default_factory=list,
        description="MCP server configs (MCPServerConfig) to connect at startup",
    )

    developer_instructions: str | None = None
    user_instructions: str | None = None
    debug: bool = False

    # --- Derived properties ---------------------------------------------------

    @property
    def api_key(self) -> str | None:
        return os.environ.get("OPENROUTER_API_KEY") or os.environ.get("API_KEY")

    @property
    def base_url(self) -> str:
        return os.environ.get(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        )

    @property
    def model_name(self) -> str:
        return self.model.name

    @model_name.setter
    def model_name(self, value: str) -> None:
        self.model.name = value

    @property
    def temperature(self) -> float:
        return self.model.temperature

    @property
    def context_window(self) -> int:
        return self.model.context_window

    # --- Validation -----------------------------------------------------------

    def validate_config(self) -> list[str]:
        """Return a list of configuration errors (empty if valid)."""
        errors: list[str] = []
        if not self.api_key:
            errors.append(
                "No API key found. Set OPENROUTER_API_KEY environment variable."
            )
        if not self.cwd.exists():
            errors.append(f"Working directory does not exist: {self.cwd}")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
