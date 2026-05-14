"""MCP bridge: connect FastMCP servers to the agent's ToolRegistry.

This module adapts any MCP server into the tool abstraction used by the
coding agent.  Each tool discovered on a connected server becomes an
``MCPToolAdapter`` — a ``Tool`` subclass that delegates ``execute`` to the
server over the open FastMCP client connection.

The ``MCPManager`` owns the connection lifecycle.  Create it once at
application startup, call ``connect_all(registry)`` to discover and
register tools, and call ``close()`` on shutdown.

Quick example::

    from notebooks.agent.tools.mcp_bridge import MCPManager, MCPServerConfig

    manager = MCPManager([
        MCPServerConfig(name="math", command="python", args=["math_server.py"]),
        MCPServerConfig(name="context7", url="https://mcp.context7.com/mcp"),
    ])
    await manager.connect_all(registry)
    # ... agent runs ...
    await manager.close()

Transports supported:

* **stdio** — a local Python script spawned as a subprocess.
  Set ``command`` + ``args``; ``url`` must be ``None``.
* **HTTP (Streamable HTTP / SSE)** — a remote MCP server.
  Set ``url``; ``command``/``args`` must be ``None``.

See the MCP notebook (``notebooks/tooling/mcp.ipynb``) for background on
the FastMCP protocol, server construction, and available public servers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from fastmcp import Client
from fastmcp.client import PythonStdioTransport, StreamableHttpTransport
from pydantic import BaseModel

from notebooks.agent.tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from notebooks.agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

# MCP tool names are namespaced with their server name to avoid collisions.
# e.g. server "context7" + tool "resolve-library-id" → "context7__resolve-library-id"
_SEP = "__"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class MCPServerConfig:
    """Connection parameters for one MCP server.

    Parameters
    ----------
    name:
        Human-readable server name.  Used as the tool-name prefix and in
        ``/mcp`` status output.
    command:
        Executable to spawn for stdio transport (e.g. ``"python"``).
        Mutually exclusive with *url*.
    args:
        Arguments for the subprocess (e.g. ``["server.py"]``).
    env:
        Extra environment variables forwarded to the subprocess.
    url:
        URL for HTTP transport (e.g. ``"https://mcp.context7.com/mcp"``).
        Mutually exclusive with *command*.
    headers:
        Extra HTTP headers (e.g. ``{"Authorization": "Bearer …"}``).
    """

    name: str
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] | None = None
    url: str | None = None
    headers: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if self.command is None and self.url is None:
            raise ValueError(
                f"MCPServerConfig '{self.name}': must set either 'command' (stdio) or 'url' (http)"
            )
        if self.command is not None and self.url is not None:
            raise ValueError(
                f"MCPServerConfig '{self.name}': 'command' and 'url' are mutually exclusive"
            )

    @property
    def transport_kind(self) -> str:
        return "stdio" if self.command else "http"


# ---------------------------------------------------------------------------
# MCPToolAdapter
# ---------------------------------------------------------------------------


class MCPToolAdapter(Tool):
    """A ``Tool`` that delegates execution to an MCP server tool.

    Each instance wraps one tool discovered via ``client.list_tools()``.
    The ``MCPManager`` holds the live ``Client`` and passes it in at
    construction time.

    Parameters
    ----------
    server_name:
        The originating server's name (used for namespacing and display).
    mcp_tool_name:
        The tool's original name as reported by the server.
    description:
        Tool description from the server.
    input_schema:
        JSON Schema dict from ``mcp.types.Tool.inputSchema``.
    client:
        The open ``fastmcp.Client`` to call through.
    """

    kind = ToolKind.NETWORK  # MCP tools are always treated as network calls

    def __init__(
        self,
        server_name: str,
        mcp_tool_name: str,
        description: str,
        input_schema: dict[str, Any],
        client: Client,
        config: Any,  # notebooks.agent.config.Config
    ) -> None:
        super().__init__(config)
        self.server_name = server_name
        self.mcp_tool_name = mcp_tool_name
        self._client = client

        # Prefixed name visible to the agent and the UI
        self.name = f"{server_name}{_SEP}{mcp_tool_name}"
        self.description = f"[{server_name}] {description}" if description else f"[{server_name}] {mcp_tool_name}"

        # Use a raw dict schema so we don't need a Pydantic model per tool
        self.schema = {"parameters": input_schema}

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        try:
            result = await self._client.call_tool(
                self.mcp_tool_name, invocation.params
            )
        except Exception as exc:
            return ToolResult.error_result(
                f"MCP call failed ({self.server_name}/{self.mcp_tool_name}): {exc}"
            )

        if result.is_error:
            # content items are TextContent; join them all
            error_text = "\n".join(
                getattr(item, "text", str(item)) for item in result.content
            )
            return ToolResult.error_result(error_text)

        # Collect all text content items
        output_parts: list[str] = []
        for item in result.content:
            text = getattr(item, "text", None)
            if text is not None:
                output_parts.append(str(text))
            else:
                # Non-text content (images, etc.) — stringify the type
                output_parts.append(f"[{type(item).__name__} content]")

        output = "\n".join(output_parts) if output_parts else str(result.data)
        return ToolResult.success_result(
            output,
            metadata={
                "server": self.server_name,
                "tool": self.mcp_tool_name,
            },
        )


# ---------------------------------------------------------------------------
# MCPManager
# ---------------------------------------------------------------------------


class MCPManager:
    """Manages the lifecycle of one or more MCP server connections.

    Owns open ``fastmcp.Client`` instances for the duration of the
    application session and registers the discovered tools into the
    provided ``ToolRegistry``.

    Parameters
    ----------
    servers:
        List of server configurations to connect to.
    """

    def __init__(self, servers: list[MCPServerConfig]) -> None:
        self.servers = servers
        # server_name → open Client
        self._clients: dict[str, Client] = {}
        # server_name → list of registered tool names
        self._registered: dict[str, list[str]] = {}

    async def connect_all(
        self,
        registry: ToolRegistry,
        *,
        skip_errors: bool = True,
    ) -> dict[str, list[str]]:
        """Connect to all configured servers and register their tools.

        Parameters
        ----------
        registry:
            The ``ToolRegistry`` to register discovered tools into.
        skip_errors:
            When ``True`` (default), connection failures log a warning and
            continue rather than raising.  Useful for startup when a server
            may be temporarily unavailable.

        Returns
        -------
        dict[str, list[str]]
            Mapping of ``server_name → [registered tool names]``.
        """
        results: dict[str, list[str]] = {}
        for server_cfg in self.servers:
            try:
                names = await self._connect_one(server_cfg, registry)
                results[server_cfg.name] = names
                logger.info(
                    "Connected to MCP server %r, registered %d tools: %s",
                    server_cfg.name,
                    len(names),
                    names,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to connect to MCP server %r: %s", server_cfg.name, exc
                )
                if not skip_errors:
                    raise
                results[server_cfg.name] = []
        return results

    async def _connect_one(
        self,
        cfg: MCPServerConfig,
        registry: ToolRegistry,
    ) -> list[str]:
        """Open a client, list tools, register adapters.  Returns tool names."""
        transport = self._make_transport(cfg)
        client = Client(transport)
        # Enter the context manager to open the connection
        await client.__aenter__()
        self._clients[cfg.name] = client

        mcp_tools = await client.list_tools()
        registered_names: list[str] = []

        for mcp_tool in mcp_tools:
            adapter = MCPToolAdapter(
                server_name=cfg.name,
                mcp_tool_name=mcp_tool.name,
                description=mcp_tool.description or "",
                input_schema=mcp_tool.inputSchema,
                client=client,
                config=registry.config,
            )
            registry.register(adapter)
            registered_names.append(adapter.name)

        self._registered[cfg.name] = registered_names
        return registered_names

    @staticmethod
    def _make_transport(cfg: MCPServerConfig) -> Any:
        if cfg.url:
            return StreamableHttpTransport(
                url=cfg.url,
                headers=cfg.headers,
            )
        # stdio
        assert cfg.command is not None
        return PythonStdioTransport(
            script_path=cfg.args[0] if cfg.args else cfg.command,
            args=cfg.args[1:] if cfg.args else [],
            env=cfg.env,
        )

    async def close(self) -> None:
        """Close all open client connections."""
        for name, client in list(self._clients.items()):
            try:
                await client.__aexit__(None, None, None)
                logger.debug("Closed MCP client for %r", name)
            except Exception as exc:
                logger.warning("Error closing MCP client %r: %s", name, exc)
        self._clients.clear()

    def status(self) -> dict[str, Any]:
        """Return a summary of connected servers and their registered tools."""
        return {
            name: {
                "connected": name in self._clients,
                "tools": self._registered.get(name, []),
            }
            for name in (cfg.name for cfg in self.servers)
        }
