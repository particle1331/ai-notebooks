"""Slash command parser and handler for the agent UI.

Commands are intercepted in ``_on_send`` *before* being routed to the
agent.  Each command returns a :class:`CommandResult` that tells the UI
what to display and whether a session operation occurred.

Supported commands::

    /help               List all commands
    /tools              List registered tools with descriptions
    /stats              Show token usage, turn count, context %
    /config             Show current config (model, approval, cwd)
    /save [name]        Save the current session to disk
    /resume [name]      Load a saved session from disk
    /sessions           List all saved sessions
    /clear              Reset session (keep config, lose history)
    /mcp                Show MCP server connection status

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from notebooks.agent.agent import Agent
    from notebooks.agent.session import Session
    from notebooks.agent.tools.mcp_bridge import MCPManager


_HELP_TEXT = """\
Available commands:
  /help               Show this message
  /tools              List all registered tools
  /stats              Token usage and turn count
  /save [name]        Save session to disk (default name: "session")
  /resume [name]      Load a saved session (default name: "session")
  /sessions           List all saved sessions
  /clear              Reset conversation history
  /config             Show current configuration
  /mcp                Show MCP server connection status\
"""


@dataclass
class CommandResult:
    """Return value from a slash command handler."""

    # Text to display as a system message in the feed (empty = nothing shown)
    message: str = ""
    # If True the session was replaced and the caller should rebuild the agent
    session_replaced: bool = False
    # The new session (only set when session_replaced=True)
    new_session: object | None = None  # Session, but avoid circular import
    # If True the command is unknown and should be forwarded to the agent
    not_a_command: bool = False


def handle_command(
    raw: str,
    agent: Agent,
    session: Session,
    mcp_manager: MCPManager | None = None,
) -> CommandResult:
    """Parse and execute a slash command.

    Parameters
    ----------
    raw:
        The raw input string (must start with ``/``).
    agent:
        The current agent instance (used to access the session and registry).
    session:
        The current session (for save/load/clear operations).
    mcp_manager:
        Optional :class:`MCPManager` instance for the ``/mcp`` command.

    Returns
    -------
    CommandResult
        Describes what the UI should do next.
    """
    parts = raw.strip().split(None, 1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    # ------------------------------------------------------------------ #
    #  /help                                                               #
    # ------------------------------------------------------------------ #
    if cmd == "/help":
        return CommandResult(message=_HELP_TEXT)

    # ------------------------------------------------------------------ #
    #  /tools                                                              #
    # ------------------------------------------------------------------ #
    if cmd == "/tools":
        tools = session.registry.get_tools()
        if not tools:
            return CommandResult(message="No tools registered.")
        lines = ["Registered tools:"]
        for t in tools:
            lines.append(f"  {t.name} [{t.kind.value}]  —  {t.description}")
        return CommandResult(message="\n".join(lines))

    # ------------------------------------------------------------------ #
    #  /stats                                                              #
    # ------------------------------------------------------------------ #
    if cmd == "/stats":
        usage = session.total_usage
        ctx = session.config.context_window
        pct = (usage.prompt_tokens / ctx * 100) if ctx else 0
        lines = [
            f"Turns:              {session.turn_count}",
            f"Prompt tokens:      {usage.prompt_tokens:,}",
            f"Completion tokens:  {usage.completion_tokens:,}",
            f"Total tokens:       {usage.total_tokens:,}",
            f"Cached tokens:      {usage.cached_tokens:,}",
            f"Context usage:      {pct:.1f}% of {ctx:,}",
        ]
        return CommandResult(message="\n".join(lines))

    # ------------------------------------------------------------------ #
    #  /config                                                             #
    # ------------------------------------------------------------------ #
    if cmd == "/config":
        cfg = session.config
        lines = [
            f"Model:    {cfg.model_name}",
            f"Approval: {cfg.approval.value}",
            f"CWD:      {cfg.cwd}",
            f"Max turns:{cfg.max_turns}",
        ]
        if cfg.developer_instructions:
            lines.append(f"Dev instructions: {cfg.developer_instructions[:80]}…")
        if cfg.user_instructions:
            lines.append(f"User instructions: {cfg.user_instructions[:80]}…")
        return CommandResult(message="\n".join(lines))

    # ------------------------------------------------------------------ #
    #  /clear                                                              #
    # ------------------------------------------------------------------ #
    if cmd == "/clear":
        session.reset()
        return CommandResult(message="Session cleared. Conversation history reset.")

    # ------------------------------------------------------------------ #
    #  /sessions                                                           #
    # ------------------------------------------------------------------ #
    if cmd == "/sessions":
        from notebooks.agent.session import Session as Sess  # local import

        saved = Sess.list_saved()
        if not saved:
            return CommandResult(message="No saved sessions found in ~/.cda/sessions/")
        return CommandResult(message="Saved sessions:\n" + "\n".join(f"  {s}" for s in saved))

    # ------------------------------------------------------------------ #
    #  /save [name]                                                        #
    # ------------------------------------------------------------------ #
    if cmd == "/save":
        name = arg or "session"
        try:
            path = session.save(name)
            return CommandResult(message=f"Session saved to {path}")
        except Exception as exc:
            return CommandResult(message=f"Save failed: {exc}")

    # ------------------------------------------------------------------ #
    #  /resume [name]                                                      #
    # ------------------------------------------------------------------ #
    if cmd == "/resume":
        name = arg or "session"
        try:
            from notebooks.agent.session import Session as Sess  # local import

            new_session = Sess.load(name, session.config)
            return CommandResult(
                message=f"Session '{name}' loaded ({new_session.turn_count} turns, "
                f"{new_session.total_usage.total_tokens:,} tokens).",
                session_replaced=True,
                new_session=new_session,
            )
        except FileNotFoundError:
            return CommandResult(message=f"Session '{name}' not found. Use /sessions to list saved sessions.")
        except Exception as exc:
            return CommandResult(message=f"Resume failed: {exc}")

    # ------------------------------------------------------------------ #
    #  /mcp                                                               #
    # ------------------------------------------------------------------ #
    if cmd == "/mcp":
        if mcp_manager is None:
            return CommandResult(message="No MCP manager configured.")
        status = mcp_manager.status()
        if not status:
            return CommandResult(message="No MCP servers configured.")
        lines = ["MCP servers:"]
        for srv_name, info in status.items():
            connected = "connected" if info["connected"] else "disconnected"
            tool_names = info["tools"]
            n = len(tool_names)
            lines.append(f"  {srv_name}  [{connected}]  —  {n} tool(s)")
            for t in tool_names:
                lines.append(f"    • {t}")
        return CommandResult(message="\n".join(lines))

    # ------------------------------------------------------------------ #
    #  Unknown command → pass through to the agent                        #
    # ------------------------------------------------------------------ #
    return CommandResult(not_a_command=True)
