"""Approval system for tool invocations.

Decides which tool calls need user approval and which can auto-execute.
This is a UX guardrail — not a security sandbox. The actual approval UI
(prompting the user) lives elsewhere; this module only returns yes/no.
"""

from __future__ import annotations

import logging
import re

from notebooks.agent.config import ApprovalPolicy, Config
from notebooks.agent.tools.base import Tool, ToolKind

logger = logging.getLogger(__name__)


class ApprovalManager:
    """Decides whether tool calls need user approval."""

    def __init__(self, config: Config) -> None:
        self._config = config

        self._safe_commands: set[str] = {
            "ls",
            "cat",
            "head",
            "tail",
            "grep",
            "find",
            "wc",
            "echo",
            "pwd",
            "which",
            "env",
            "whoami",
            "date",
            "file",
            "stat",
            "du",
            "df",
            "uname",
            "python --version",
            "git status",
            "git log",
            "git diff",
        }

        self._dangerous_patterns: list[str] = [
            "rm -rf",
            "rm -r",
            "sudo",
            "chmod 777",
            "kill -9",
            "pkill",
            "mkfs",
            "dd if=",
            "shutdown",
            "reboot",
            "> /dev/",
            "| sh",
            "| bash",
            "curl.*| sh",
            "wget.*| sh",
        ]

    # --- Public API -----------------------------------------------------------

    def needs_approval(self, tool: Tool, params: dict) -> bool:
        """Decide whether *tool* called with *params* requires user approval.

        Returns ``True`` when the invocation must be confirmed by the user
        before execution, ``False`` when it can proceed automatically.
        """
        policy = self._config.approval

        # YOLO — skip all approval
        if policy == ApprovalPolicy.YOLO:
            logger.debug("YOLO mode: auto-approving %s", tool.name)
            return False

        # NEVER — require approval for everything
        if policy == ApprovalPolicy.NEVER:
            logger.debug("NEVER mode: requiring approval for %s", tool.name)
            return True

        # Reads are always safe regardless of policy
        if tool.kind == ToolKind.READ:
            logger.debug("READ tool %s: auto-approved", tool.name)
            return False

        # AUTO mode — be permissive, only block dangerous shell commands
        if policy == ApprovalPolicy.AUTO:
            if tool.kind == ToolKind.SHELL:
                command = self._extract_command(params)
                if self.is_dangerous_command(command):
                    logger.debug(
                        "AUTO mode: dangerous shell command requires approval: %s",
                        command,
                    )
                    return True
                if self.is_safe_command(command):
                    logger.debug(
                        "AUTO mode: safe shell command auto-approved: %s", command
                    )
                    return False
                # Neither dangerous nor explicitly safe — auto-approve in AUTO
                logger.debug(
                    "AUTO mode: shell command auto-approved (not dangerous): %s",
                    command,
                )
                return False
            # WRITE, NETWORK, MEMORY — auto-approve in AUTO mode
            logger.debug("AUTO mode: auto-approving %s (%s)", tool.name, tool.kind)
            return False

        # ON_REQUEST (default) — require approval for mutating operations
        if tool.kind == ToolKind.SHELL:
            command = self._extract_command(params)
            if self.is_safe_command(command):
                logger.debug(
                    "ON_REQUEST mode: safe shell command auto-approved: %s", command
                )
                return False
            logger.debug(
                "ON_REQUEST mode: shell command requires approval: %s", command
            )
            return True

        # WRITE, NETWORK, MEMORY — require approval in ON_REQUEST
        logger.debug(
            "ON_REQUEST mode: %s tool %s requires approval", tool.kind, tool.name
        )
        return True

    def is_dangerous_command(self, command: str) -> bool:
        """Check if *command* matches any dangerous pattern.

        Uses simple substring matching for literal patterns and regex
        matching for patterns containing ``.*``.
        """
        cmd = command.strip()
        for pattern in self._dangerous_patterns:
            if ".*" in pattern:
                # Treat as regex
                if re.search(pattern, cmd):
                    return True
            else:
                if pattern in cmd:
                    return True
        return False

    def is_safe_command(self, command: str) -> bool:
        """Check if *command* starts with a known safe command.

        Matches the first word (e.g. ``"ls"``) or multi-word phrase
        (e.g. ``"git status"``) against the safe commands set.
        """
        cmd = command.strip()
        if not cmd:
            return False

        # Check multi-word safe commands first (longest match wins)
        for safe in sorted(self._safe_commands, key=len, reverse=True):
            if " " in safe:
                # Multi-word: command must start with the exact phrase
                if cmd == safe or cmd.startswith(safe + " "):
                    return True
            else:
                # Single-word: first token must match exactly
                first_word = cmd.split()[0]
                if first_word == safe:
                    return True

        return False

    def get_approval_reason(self, tool: Tool, params: dict) -> str:
        """Return a human-readable reason why approval is needed.

        Intended for display in the approval dialog. Returns a generic
        message if no specific reason can be determined.
        """
        if tool.kind == ToolKind.SHELL:
            command = self._extract_command(params)
            # Check for specific dangerous pattern
            for pattern in self._dangerous_patterns:
                if ".*" in pattern:
                    if re.search(pattern, command):
                        # Show the literal part before .*
                        label = pattern.split(".*")[0].strip()
                        return f"Dangerous command detected: {label}... | sh"
                else:
                    if pattern in command:
                        return f"Dangerous command detected: {pattern}"
            return "Shell command requires approval"

        if tool.kind == ToolKind.WRITE:
            return "File write requires approval"

        if tool.kind == ToolKind.NETWORK:
            return "Network access requires approval"

        if tool.kind == ToolKind.MEMORY:
            return "Memory modification requires approval"

        return f"{tool.name} requires approval"

    # --- Internal helpers -----------------------------------------------------

    @staticmethod
    def _extract_command(params: dict) -> str:
        """Pull the shell command string from tool params."""
        return params.get("command", "")
