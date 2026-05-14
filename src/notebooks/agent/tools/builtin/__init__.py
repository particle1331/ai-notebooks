"""Builtin tools for the coding agent.

Provides ``get_all_builtin_tools()`` which returns every tool class
shipped with the package.  The registry calls this at startup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from notebooks.agent.tools.builtin.edit_file import EditTool
from notebooks.agent.tools.builtin.fetch_url import FetchUrlTool
from notebooks.agent.tools.builtin.glob import GlobTool
from notebooks.agent.tools.builtin.grep import GrepTool
from notebooks.agent.tools.builtin.list_dir import ListDirTool
from notebooks.agent.tools.builtin.memory import MemoryTool
from notebooks.agent.tools.builtin.read_file import ReadFileTool
from notebooks.agent.tools.builtin.shell import ShellTool
from notebooks.agent.tools.builtin.todo import TodoTool
from notebooks.agent.tools.builtin.web_search import WebSearchTool
from notebooks.agent.tools.builtin.write_file import WriteFileTool

if TYPE_CHECKING:
    from notebooks.agent.tools.base import Tool

ALL_BUILTIN_TOOLS: list[type[Tool]] = [
    ReadFileTool,
    WriteFileTool,
    EditTool,
    ShellTool,
    ListDirTool,
    GrepTool,
    GlobTool,
    FetchUrlTool,
    WebSearchTool,
    MemoryTool,
    TodoTool,
]


def get_all_builtin_tools() -> list[type[Tool]]:
    """Return all builtin tool classes."""
    return list(ALL_BUILTIN_TOOLS)
