"""Flet desktop application for the coding agent.

Entry point::

    uv run flet run src/notebooks/agent/ui/app.py

The app renders a chat-style interface:
  - A scrollable message/tool-call feed on the left
  - A text input bar at the bottom
  - A thin status bar showing turn count and token usage

The ``Agent`` runs in a background async task so the UI stays responsive
during long-running multi-turn sessions.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import flet as ft

from notebooks.agent.agent import Agent
from notebooks.agent.config import ApprovalPolicy, Config
from notebooks.agent.events import AgentEventType
from notebooks.agent.safety import ApprovalManager
from notebooks.agent.tools.mcp_bridge import MCPManager
from notebooks.agent.ui.commands import handle_command
from notebooks.agent.ui.components import (
    MessageData,
    ToolCallData,
    make_approval_dialog,
    make_message_bubble,
    make_status_bar,
    make_tool_call_card,
)


# ---------------------------------------------------------------------------
# Application state (imperative pattern)
# ---------------------------------------------------------------------------


class AgentApp:
    """Wires Flet page to the agent and manages UI state."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        # Initialize _pending_cards before any async callbacks can fire.
        self._pending_cards: dict[str, ft.Container] = {}
        self._configure_page()

        # Agent plumbing
        self.config = self._build_config()
        self.agent = Agent(self.config)
        self.approval_manager = ApprovalManager(self.config)

        # MCP manager — connect_all() is called after the layout is built so
        # connection errors can be shown as system bubbles in the feed.
        self._mcp_manager = MCPManager(self.config.mcp_servers)

        # Mutable UI state
        self._running = False
        self._turn = 0
        self._total_tokens = 0

        # Pending approval (tool call waiting for user decision)
        self._approval_future: asyncio.Future | None = None

        # Build the UI layout
        self._feed = ft.ListView(
            expand=True,
            spacing=4,
            auto_scroll=True,
            padding=ft.padding.symmetric(vertical=8, horizontal=12),
        )
        self._input = ft.TextField(
            hint_text="Ask anything, or type /help for commands…",
            expand=True,
            bgcolor="#1C1C1C",
            color=ft.Colors.WHITE,
            hint_style=ft.TextStyle(color=ft.Colors.GREY_600),
            border_color=ft.Colors.GREY_800,
            focused_border_color=ft.Colors.BLUE_400,
            multiline=True,
            min_lines=1,
            max_lines=6,
            on_submit=self._on_send,
        )
        self._send_btn = ft.IconButton(
            icon=ft.Icons.SEND,
            icon_color=ft.Colors.BLUE_400,
            on_click=self._on_send,
            tooltip="Send (Enter)",
        )
        self._status_row = ft.Row([], spacing=0)

        self._build_layout()
        self._refresh_status()

        # Connect MCP servers asynchronously after layout is rendered
        page.run_task(self._connect_mcp)

        # Close MCP connections when the page/window closes
        page.on_disconnect = self._on_disconnect

    # ------------------------------------------------------------------
    # MCP lifecycle
    # ------------------------------------------------------------------

    async def _connect_mcp(self) -> None:
        """Connect all MCP servers from Config.mcp_servers at startup."""
        if not self._mcp_manager.servers:
            return
        registry = self.agent.session.registry
        results = await self._mcp_manager.connect_all(registry, skip_errors=True)
        for srv_name, tool_names in results.items():
            if tool_names:
                self._add_message(
                    MessageData(
                        role="system",
                        content=f"MCP: connected to '{srv_name}' — {len(tool_names)} tool(s) registered.",
                    )
                )
            else:
                self._add_message(
                    MessageData(
                        role="system",
                        content=f"MCP: failed to connect to '{srv_name}' (check logs).",
                    )
                )

    async def _on_disconnect(self, e: ft.Event) -> None:  # noqa: ARG002
        """Close MCP connections when the window / tab is closed."""
        await self._mcp_manager.close()

    # ------------------------------------------------------------------
    # Page configuration
    # ------------------------------------------------------------------

    def _configure_page(self) -> None:
        self.page.title = "Coding Agent"
        self.page.bgcolor = "#121212"
        self.page.padding = 0
        self.page.window.width = 900
        self.page.window.height = 700
        self.page.window.min_width = 480
        self.page.window.min_height = 400

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    @staticmethod
    def _build_config() -> Config:
        return Config(
            cwd=Path.cwd(),
            approval=ApprovalPolicy.ON_REQUEST,
            max_turns=50,
        )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        input_row = ft.Row(
            [self._input, self._send_btn],
            spacing=8,
            alignment=ft.MainAxisAlignment.END,
        )
        input_bar = ft.Container(
            content=input_row,
            bgcolor="#181818",
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_900)),
            padding=ft.padding.symmetric(vertical=8, horizontal=12),
        )
        self.page.add(
            ft.Column(
                [
                    # Top: status bar
                    self._status_row,
                    # Middle: message feed (expands)
                    ft.Container(content=self._feed, expand=True),
                    # Bottom: input bar
                    input_bar,
                ],
                expand=True,
                spacing=0,
            )
        )

    # ------------------------------------------------------------------
    # Status bar refresh
    # ------------------------------------------------------------------

    def _refresh_status(self, running: bool = False) -> None:
        self._status_row.controls = [
            make_status_bar(
                turn=self._turn,
                total_tokens=self._total_tokens,
                model=self.config.model_name,
                running=running,
            )
        ]
        self._status_row.update()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _on_send(self, e: ft.ControlEvent | None = None) -> None:
        text = self._input.value.strip()
        if not text or self._running:
            return

        self._input.value = ""
        self._input.update()

        # ---- Slash command intercept ----------------------------------------
        if text.startswith("/"):
            result = handle_command(
                text, self.agent, self.agent.session, self._mcp_manager
            )
            if not result.not_a_command:
                if result.message:
                    self._add_message(MessageData(role="system", content=result.message))
                if result.session_replaced and result.new_session is not None:
                    self.agent.session = result.new_session  # type: ignore[assignment]
                    self._turn = result.new_session.turn_count  # type: ignore[union-attr]
                    self._total_tokens = result.new_session.total_usage.total_tokens  # type: ignore[union-attr]
                    self._refresh_status()
                return
            # Unknown slash command — fall through to agent
        # ---------------------------------------------------------------------

        self._add_message(MessageData(role="user", content=text))

        self._running = True
        self._send_btn.disabled = True
        self._send_btn.update()
        self._refresh_status(running=True)

        await self._run_agent(text)

        self._running = False
        self._send_btn.disabled = False
        self._send_btn.update()
        self._refresh_status(running=False)

    # ------------------------------------------------------------------
    # Agent runner
    # ------------------------------------------------------------------

    async def _run_agent(self, user_message: str) -> None:
        """Drive the agent and render events as they stream in."""
        current_text = ""

        # Placeholder for the streaming assistant text bubble
        text_bubble_ref: list[ft.Container] = []

        async for event in self.agent.run(user_message):
            event_type = event.type

            if event_type == AgentEventType.TEXT_DELTA:
                content = event.data.get("content", "")
                current_text += content
                if text_bubble_ref:
                    # Update the live text bubble in-place
                    bubble = text_bubble_ref[0]
                    bubble.content.value = current_text  # type: ignore[union-attr]
                    bubble.update()
                else:
                    # Create the bubble on first chunk
                    bubble = self._add_message(
                        MessageData(role="assistant", content=current_text)
                    )
                    text_bubble_ref.append(bubble)

            elif event_type == AgentEventType.TEXT_COMPLETE:
                current_text = ""
                text_bubble_ref.clear()

            elif event_type == AgentEventType.TOOL_CALL_START:
                call_id = event.data.get("call_id", "")
                name = event.data.get("name", "")
                arguments = event.data.get("arguments", {})
                card = self._add_tool_card(
                    ToolCallData(call_id=call_id, name=name, arguments=arguments)
                )
                # Store card by call_id for later update
                self._pending_cards[call_id] = card

            elif event_type == AgentEventType.TOOL_CALL_COMPLETE:
                call_id = event.data.get("call_id", "")
                success = event.data.get("success", True)
                output = event.data.get("output", "")
                error = event.data.get("error")
                card = self._pending_cards.pop(call_id, None)
                if card is not None:
                    self._update_tool_card(
                        card,
                        ToolCallData(
                            call_id=call_id,
                            name=event.data.get("name", ""),
                            arguments={},
                            output=output,
                            error=error,
                            success=success,
                        ),
                    )

            elif event_type == AgentEventType.AGENT_END:
                self._turn += 1
                usage = event.data.get("usage") or {}
                self._total_tokens += usage.get("total_tokens", 0)

            elif event_type == AgentEventType.AGENT_ERROR:
                error_msg = event.data.get("error", "Unknown error")
                self._add_message(MessageData(role="system", content=f"⚠ {error_msg}"))

    # ------------------------------------------------------------------
    # Feed helpers
    # ------------------------------------------------------------------

    def _add_message(self, msg: MessageData) -> ft.Container:
        bubble = make_message_bubble(msg)
        self._feed.controls.append(bubble)
        self._feed.update()
        return bubble

    def _add_tool_card(self, tc: ToolCallData) -> ft.Container:
        card = make_tool_call_card(tc)
        self._feed.controls.append(card)
        self._feed.update()
        return card

    def _update_tool_card(self, card: ft.Container, tc: ToolCallData) -> None:
        """Replace the in-progress card with a finished one."""
        new_card = make_tool_call_card(tc)
        idx = self._feed.controls.index(card)
        self._feed.controls[idx] = new_card
        self._feed.update()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(page: ft.Page) -> None:
    AgentApp(page)


if __name__ == "__main__":
    ft.run(main)
