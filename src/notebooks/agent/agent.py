"""Core agent module: the agentic loop (think → act → observe → repeat).

The Agent class orchestrates multi-turn conversations with an LLM,
processing streamed responses and invoking tools when requested.
It yields AgentEvent objects so callers can render output progressively.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from notebooks.agent.config import Config
from notebooks.agent.events import (
    AgentEvent,
    AgentEventType,
    StreamEventType,
    TokenUsage,
    ToolCall,
    ToolResultMessage,
)
from notebooks.agent.session import Session

logger = logging.getLogger(__name__)


class Agent:
    """AI coding agent with an async agentic loop.

    Usage::

        agent = Agent(config)
        async for event in agent.run("Fix the bug in main.py"):
            if event.type == AgentEventType.TEXT_DELTA:
                print(event.data["content"], end="")
    """

    def __init__(
        self,
        config: Config | None = None,
        session: Session | None = None,
    ) -> None:
        self.config = config or Config()
        self.session = session or Session(self.config)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    async def run(self, user_message: str) -> AsyncGenerator[AgentEvent, None]:
        """Run the agent on a user message, yielding lifecycle events.

        This is the main entry point.  It wraps :meth:`_agentic_loop` with
        start / end / error bookkeeping so callers always get a clean
        event stream.
        """
        yield AgentEvent.agent_start(user_message)
        self.session.add_user_message(user_message)

        try:
            response: str | None = None
            async for event in self._agentic_loop():
                yield event
                # Capture the final assistant text for the end event
                if event.data.get("content") is not None and hasattr(event, "type"):
                    if event.type == AgentEventType.TEXT_COMPLETE:
                        response = event.data["content"]

            yield AgentEvent.agent_end(response, self.session.total_usage)

        except Exception as e:
            logger.exception("Agent run failed")
            yield AgentEvent.agent_error(str(e))

    # ------------------------------------------------------------------ #
    #  Agentic loop                                                        #
    # ------------------------------------------------------------------ #

    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent, None]:
        """Multi-turn loop: call LLM, execute tools, repeat.

        Yields :class:`AgentEvent` objects for each meaningful step
        (text deltas, tool invocations, completions).
        """
        for turn in range(self.config.max_turns):
            self.session.turn_count += 1
            logger.debug("Turn %d / %d", self.session.turn_count, self.config.max_turns)

            # ----- Stream the LLM response --------------------------------
            accumulated_text = ""
            tool_calls: list[ToolCall] = []
            usage: TokenUsage | None = None
            error_message: str | None = None

            stream = self.session.client.chat_completion(
                self.session.get_messages(),
                tools=self.session.get_tool_schemas(),
            )

            async for event in stream:
                if event.type == StreamEventType.TEXT_DELTA:
                    content = event.text_delta.content if event.text_delta else ""
                    accumulated_text += content
                    yield AgentEvent.text_delta(content)

                elif event.type == StreamEventType.TOOL_CALL_COMPLETE:
                    if event.tool_call is not None:
                        tool_calls.append(event.tool_call)

                elif event.type == StreamEventType.MESSAGE_COMPLETE:
                    if event.usage is not None:
                        usage = event.usage
                        self.session.track_usage(usage)

                elif event.type == StreamEventType.ERROR:
                    error_message = event.error
                    yield AgentEvent.agent_error(error_message or "Unknown LLM error")

            # ----- Handle errors from the stream --------------------------
            if error_message is not None:
                return

            # ----- Emit text-complete if we accumulated any text ----------
            if accumulated_text:
                yield AgentEvent.text_complete(accumulated_text)

            # ----- Add assistant message to session -----------------------
            assistant_msg = self._build_assistant_message(accumulated_text, tool_calls)
            if tool_calls:
                self.session.add_assistant_message(
                    content=assistant_msg.get("content", ""),
                    tool_calls=[
                        {
                            "id": tc.call_id,
                            "name": tc.name,
                            "arguments": tc.arguments,
                        }
                        for tc in tool_calls
                    ],
                )
            else:
                self.session.add_assistant_message(
                    content=assistant_msg.get("content", ""),
                )

            # ----- If no tool calls, the agent is done --------------------
            if not tool_calls:
                return

            # ----- Execute each tool call ---------------------------------
            for tc in tool_calls:
                name = tc.name or ""
                yield AgentEvent.tool_call_start(tc.call_id, name, tc.arguments)

                result = await self.session.registry.invoke(
                    name, tc.arguments, self.config.cwd
                )

                yield AgentEvent.tool_call_complete(tc.call_id, name, result)

                tool_result_msg = ToolResultMessage(
                    tool_call_id=tc.call_id,
                    content=result.to_model_output(),
                    is_error=not result.success,
                )
                self.session.add_tool_result(tool_result_msg)

            # Loop continues — model sees the tool results next turn

        # Max turns exceeded
        yield AgentEvent.agent_error(
            f"Agent exceeded maximum number of turns ({self.config.max_turns})"
        )

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_assistant_message(
        text: str | None,
        tool_calls: list[ToolCall],
    ) -> dict:
        """Build an assistant message dict in OpenAI format.

        Parameters
        ----------
        text : str | None
            The text content of the assistant reply.
        tool_calls : list[ToolCall]
            Completed tool calls from the LLM response.

        Returns
        -------
        dict
            Message dict with ``role``, ``content``, and optionally
            ``tool_calls``.
        """
        message: dict = {
            "role": "assistant",
            "content": text or "",
        }
        if tool_calls:
            message["tool_calls"] = [
                {
                    "id": tc.call_id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                }
                for tc in tool_calls
            ]
        return message
