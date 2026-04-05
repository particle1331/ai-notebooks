# src/notebooks/agent/__init__.py
"""Async AI coding agent package.

Quick start::

    from notebooks.agent import Agent, Config

    agent = Agent()
    async for event in agent.run("List the Python files here"):
        print(event)

To run the Flet desktop app::

    uv run flet run src/notebooks/agent/ui/app.py
"""

from notebooks.agent.agent import Agent
from notebooks.agent.client import LLMClient
from notebooks.agent.compaction import ChatCompactor
from notebooks.agent.config import ApprovalPolicy, Config, ModelConfig
from notebooks.agent.context import ContextManager
from notebooks.agent.events import AgentEvent, AgentEventType, TokenUsage
from notebooks.agent.loop_detector import LoopDetector
from notebooks.agent.safety import ApprovalManager
from notebooks.agent.session import Session
from notebooks.agent.tools import (
    BUILTIN_ROLES,
    MCPManager,
    MCPServerConfig,
    MCPToolAdapter,
    SubAgentTool,
    Tool,
    ToolKind,
    ToolRegistry,
    ToolResult,
    create_default_registry,
)

__all__ = [
    # Core
    "Agent",
    "Session",
    "LLMClient",
    # Config
    "Config",
    "ModelConfig",
    "ApprovalPolicy",
    # Events
    "AgentEvent",
    "AgentEventType",
    "TokenUsage",
    # Hardening
    "ContextManager",
    "ChatCompactor",
    "LoopDetector",
    "ApprovalManager",
    # Tools
    "Tool",
    "ToolKind",
    "ToolResult",
    "ToolRegistry",
    "create_default_registry",
    "SubAgentTool",
    "BUILTIN_ROLES",
    # MCP
    "MCPServerConfig",
    "MCPToolAdapter",
    "MCPManager",
]
