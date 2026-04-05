"""UI component library for the coding agent desktop app.

Provides reusable Flet controls for the chat-style interface:
  - ``MessageBubble``    — renders a single conversation message
  - ``ToolCallCard``     — renders a tool invocation with status
  - ``StatusBar``        — shows token usage and turn count
  - ``ApprovalDialog``   — asks the user to approve / reject a tool call
"""

from __future__ import annotations

from dataclasses import dataclass, field

import flet as ft


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class MessageData:
    """Data needed to render one chat message."""

    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class ToolCallData:
    """Data needed to render one tool invocation card."""

    call_id: str
    name: str
    arguments: dict
    output: str = ""
    error: str | None = None
    success: bool | None = None  # None = in-progress


# ---------------------------------------------------------------------------
# MessageBubble
# ---------------------------------------------------------------------------


def make_message_bubble(msg: MessageData) -> ft.Container:
    """Return a chat-bubble Container for *msg*.

    User messages are right-aligned with a blue background.
    Assistant messages are left-aligned with a dark-grey background.
    System messages are centered in muted italics.
    """
    if msg.role == "system":
        return ft.Container(
            content=ft.Text(
                msg.content,
                italic=True,
                size=12,
                color=ft.Colors.GREY_500,
                text_align=ft.TextAlign.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=4, horizontal=16),
            alignment=ft.Alignment(0, 0),
        )

    is_user = msg.role == "user"
    bubble_color = "#1565C0" if is_user else "#2D2D2D"
    align = ft.Alignment(1, 0) if is_user else ft.Alignment(-1, 0)

    return ft.Container(
        content=ft.Text(
            msg.content,
            selectable=True,
            size=14,
            color=ft.Colors.WHITE,
        ),
        bgcolor=bubble_color,
        border_radius=ft.border_radius.all(10),
        padding=ft.padding.symmetric(vertical=10, horizontal=14),
        alignment=align,
        margin=ft.margin.only(
            left=80 if is_user else 0,
            right=0 if is_user else 80,
            top=2,
            bottom=2,
        ),
    )


# ---------------------------------------------------------------------------
# ToolCallCard
# ---------------------------------------------------------------------------


def make_tool_call_card(tc: ToolCallData) -> ft.Container:
    """Return a compact card for a tool invocation.

    Shows: tool name + status icon (spinner / check / X), arguments
    (collapsed), and output (collapsed when long).
    """
    # Status indicator
    if tc.success is None:
        status_icon = ft.ProgressRing(width=14, height=14, stroke_width=2)
    elif tc.success:
        status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=16)
    else:
        status_icon = ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_400, size=16)

    # MCP tools are namespaced as "server__tool"; use a distinct accent color.
    name_color = ft.Colors.PURPLE_200 if "__" in tc.name else ft.Colors.BLUE_200

    # Arguments as a single truncated line
    args_str = ", ".join(f"{k}={repr(v)[:40]}" for k, v in tc.arguments.items())

    # Output / error text
    if tc.error:
        output_text = ft.Text(
            f"Error: {tc.error}",
            size=11,
            color=ft.Colors.RED_300,
            selectable=True,
        )
    elif tc.output:
        # Trim very long outputs
        display = tc.output if len(tc.output) <= 500 else tc.output[:500] + "\n…"
        output_text = ft.Text(
            display,
            size=11,
            color=ft.Colors.GREY_300,
            selectable=True,
            font_family="monospace",
        )
    else:
        output_text = ft.Text("(no output)", size=11, color=ft.Colors.GREY_600, italic=True)

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        status_icon,
                        ft.Text(
                            tc.name,
                            weight=ft.FontWeight.BOLD,
                            size=13,
                            color=name_color,
                        ),
                        ft.Text(
                            f"({args_str})",
                            size=11,
                            color=ft.Colors.GREY_500,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
                        ),
                    ],
                    spacing=6,
                ),
                output_text,
            ],
            spacing=4,
            tight=True,
        ),
        bgcolor="#1A1A1A",
        border=ft.border.all(1, ft.Colors.GREY_800),
        border_radius=6,
        padding=ft.padding.symmetric(vertical=8, horizontal=12),
        margin=ft.margin.only(top=2, bottom=2),
    )


# ---------------------------------------------------------------------------
# StatusBar
# ---------------------------------------------------------------------------


def make_status_bar(
    turn: int,
    total_tokens: int,
    model: str,
    running: bool = False,
) -> ft.Container:
    """Return a thin status bar showing usage stats."""
    parts: list[ft.Control] = [
        ft.Text(model, size=11, color=ft.Colors.GREY_500),
        ft.Text("·", size=11, color=ft.Colors.GREY_700),
        ft.Text(f"turn {turn}", size=11, color=ft.Colors.GREY_500),
        ft.Text("·", size=11, color=ft.Colors.GREY_700),
        ft.Text(f"{total_tokens:,} tok", size=11, color=ft.Colors.GREY_500),
    ]
    if running:
        parts.append(ft.ProgressRing(width=10, height=10, stroke_width=1.5))

    return ft.Container(
        content=ft.Row(controls=parts, spacing=4),
        padding=ft.padding.symmetric(vertical=4, horizontal=12),
        bgcolor="#111111",
    )


# ---------------------------------------------------------------------------
# ApprovalDialog
# ---------------------------------------------------------------------------


def make_approval_dialog(
    tool_name: str,
    reason: str,
    on_approve: ft.ControlEventHandler,
    on_reject: ft.ControlEventHandler,
) -> ft.AlertDialog:
    """Return an AlertDialog that asks the user to approve a tool call."""
    return ft.AlertDialog(
        modal=True,
        title=ft.Text("Approve tool call?", size=16),
        content=ft.Column(
            [
                ft.Text(
                    f"Tool: {tool_name}",
                    weight=ft.FontWeight.BOLD,
                    size=14,
                ),
                ft.Text(reason, size=13, color=ft.Colors.GREY_300),
            ],
            tight=True,
            spacing=6,
        ),
        actions=[
            ft.FilledButton("Approve", on_click=on_approve),
            ft.TextButton("Reject", on_click=on_reject),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
