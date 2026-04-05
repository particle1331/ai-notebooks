"""Context compaction via LLM-powered conversation summarization.

When the conversation history grows too long, the compactor summarizes
older messages into a concise summary and replaces them — keeping the
system prompt and recent messages intact.
"""

from __future__ import annotations

import logging
from typing import Any

from notebooks.agent.client import LLMClient
from notebooks.agent.config import Config
from notebooks.agent.events import StreamEventType

logger = logging.getLogger(__name__)

# Maximum characters to keep per message when formatting for summarization.
_MAX_MESSAGE_CHARS = 2000

_SUMMARIZER_SYSTEM_PROMPT = (
    "You are a conversation summarizer for a coding agent session. "
    "Your job is to produce a concise, accurate summary of a conversation "
    "between a user and an AI coding assistant.\n\n"
    "Guidelines:\n"
    "- Summarize the key actions taken, files modified, and decisions made.\n"
    "- Preserve important details like file paths, error messages, and "
    "short code snippets.\n"
    "- Note any unresolved issues or pending tasks.\n"
    "- Keep the summary under 500 words.\n"
    "- Use bullet points for clarity."
)


class ChatCompactor:
    """Compacts conversation history by summarizing old messages with the LLM.

    When the message list grows beyond a manageable size, :meth:`compact`
    replaces the middle portion of the conversation with a single summary
    message produced by the LLM, preserving the system prompt and the most
    recent messages.

    Parameters
    ----------
    client : LLMClient
        The LLM client used for generating summaries.
    config : Config
        Agent configuration.
    """

    def __init__(self, client: LLMClient, config: Config) -> None:
        self.client = client
        self.config = config

    async def compact(
        self,
        messages: list[dict[str, Any]],
        keep_last: int = 10,
    ) -> list[dict[str, Any]]:
        """Compact conversation history by summarizing older messages.

        Keeps the system message (index 0) and the last *keep_last*
        messages.  Everything in between is replaced with a single
        summary message.

        Parameters
        ----------
        messages : list[dict]
            Full conversation message list (system prompt at index 0).
        keep_last : int
            Number of recent messages to preserve verbatim.

        Returns
        -------
        list[dict]
            Compacted message list:
            ``[system_msg, summary_msg, ...kept_tail]``.
        """
        # Need at least: system + middle messages + keep_last tail
        # If there aren't enough messages to split, return unchanged.
        if len(messages) <= keep_last + 1:
            logger.debug(
                "Not enough messages to compact (%d <= %d + 1); skipping.",
                len(messages),
                keep_last,
            )
            return messages

        system_msg = messages[0]
        middle = messages[1:-keep_last]
        tail = messages[-keep_last:]

        if not middle:
            logger.debug("No middle messages to summarize; skipping compaction.")
            return messages

        logger.debug(
            "Compacting %d middle messages (keeping system + %d tail).",
            len(middle),
            len(tail),
        )

        summary = await self._summarize(middle)

        summary_msg: dict[str, Any] = {
            "role": "user",
            "content": (
                f"[Context Summary]\n\n{summary}\n\n"
                f"[End of Summary — conversation continues below]"
            ),
        }

        return [system_msg, summary_msg, *tail]

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    async def _summarize(self, messages: list[dict[str, Any]]) -> str:
        """Summarize a list of messages using a non-streaming LLM call.

        Parameters
        ----------
        messages : list[dict]
            The conversation messages to summarize.

        Returns
        -------
        str
            A concise summary of the conversation segment.
        """
        prompt = self._build_summarization_prompt(messages)

        summary = ""
        async for event in self.client.chat_completion(prompt, stream=False):
            if (
                event.type == StreamEventType.MESSAGE_COMPLETE
                and event.text_delta is not None
            ):
                summary = event.text_delta.content
            elif event.type == StreamEventType.ERROR:
                logger.error("Summarization LLM call failed: %s", event.error)
                # Fall back to a simple truncation notice.
                summary = (
                    "Earlier conversation could not be summarized due to an "
                    "error. The conversation included "
                    f"{len(messages)} messages."
                )

        return summary

    def _build_summarization_prompt(
        self,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build the message list for the summarization LLM call.

        Each original message is formatted as ``[role]: content`` and
        very long messages are truncated to keep the summarization prompt
        reasonable.

        Parameters
        ----------
        messages : list[dict]
            The conversation messages to summarize.

        Returns
        -------
        list[dict]
            A two-message list (system + user) ready for the LLM.
        """
        formatted_parts: list[str] = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "") or ""

            # Tool-call messages may lack a content field but carry
            # structured tool_calls — represent them concisely.
            if not content and "tool_calls" in msg:
                tool_names = [
                    tc.get("function", {}).get("name", "unknown")
                    for tc in msg.get("tool_calls", [])
                ]
                content = f"[tool calls: {', '.join(tool_names)}]"

            # Truncate very long messages.
            if len(content) > _MAX_MESSAGE_CHARS:
                content = content[:_MAX_MESSAGE_CHARS] + " [... truncated]"

            formatted_parts.append(f"[{role}]: {content}")

        formatted_messages = "\n\n".join(formatted_parts)

        return [
            {"role": "system", "content": _SUMMARIZER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Summarize the following conversation:\n\n"
                    f"{formatted_messages}"
                ),
            },
        ]
