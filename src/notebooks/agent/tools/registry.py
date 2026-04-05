"""Tool registry: stores, looks up, and invokes tools.

The ToolRegistry is the central dispatcher. The agent asks it to invoke
a tool by name, and it handles validation, approval, and execution.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from notebooks.agent.config import Config
from notebooks.agent.tools.base import Tool, ToolInvocation, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self, config: Config):
        self._tools: dict[str, Tool] = {}
        self.config = config

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing tool: {tool.name}")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get_tools(self) -> list[Tool]:
        tools = list(self._tools.values())
        if self.config.allowed_tools:
            allowed = set(self.config.allowed_tools)
            tools = [t for t in tools if t.name in allowed]
        return tools

    def get_schemas(self) -> list[dict[str, Any]]:
        return [tool.to_openai_schema() for tool in self.get_tools()]

    async def invoke(
        self,
        name: str,
        params: dict[str, Any],
        cwd: Path,
        approval_callback: Callable | None = None,
    ) -> ToolResult:
        """Look up a tool by name, validate params, and execute it."""
        tool = self.get(name)
        if tool is None:
            return ToolResult.error_result(
                f"Unknown tool: {name}",
                metadata={"tool_name": name},
            )

        validation_errors = tool.validate_params(params)
        if validation_errors:
            return ToolResult.error_result(
                f"Invalid parameters: {'; '.join(validation_errors)}",
                metadata={"tool_name": name, "validation_errors": validation_errors},
            )

        invocation = ToolInvocation(params=params, cwd=cwd)

        try:
            result = await tool.execute(invocation)
        except Exception as e:
            logger.exception(f"Tool {name} raised unexpected error")
            result = ToolResult.error_result(
                f"Internal error: {str(e)}",
                metadata={"tool_name": name},
            )

        return result


def create_default_registry(config: Config) -> ToolRegistry:
    """Create a registry pre-loaded with all builtin tools."""
    from notebooks.agent.tools.builtin import get_all_builtin_tools

    registry = ToolRegistry(config)
    for tool_class in get_all_builtin_tools():
        registry.register(tool_class(config))
    return registry
