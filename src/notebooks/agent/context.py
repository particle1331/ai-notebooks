"""Context window management for the coding agent.

Tracks token usage, detects when the context window is getting full,
and prunes old messages to stay within limits.  The actual compaction
logic (LLM-based summarization) lives in ``compaction.py`` — this
module only handles bookkeeping and the mechanical pruning strategy.
"""

from __future__ import annotations

import logging
from typing import Any

from notebooks.agent.config import Config
from notebooks.agent.events import TokenUsage

logger = logging.getLogger(__name__)

# Number of most-recent messages that are never pruned.
_DEFAULT_KEEP_LAST: int = 10


class ContextManager:
    """Tracks context window usage and triggers pruning/compaction.

    Parameters
    ----------
    config : Config
        Agent configuration — ``config.context_window`` gives the model's
        maximum context length in tokens.
    compaction_threshold : float
        Fraction of the context window at which compaction is suggested
        (default 0.8 = 80 %).
    pruning_threshold : float
        Fraction of the context window at which hard pruning is triggered
        (default 0.9 = 90 %).
    keep_last : int
        Number of most-recent messages that are always preserved during
        pruning (default 10).
    """

    def __init__(
        self,
        config: Config,
        compaction_threshold: float = 0.8,
        pruning_threshold: float = 0.9,
        keep_last: int = _DEFAULT_KEEP_LAST,
    ) -> None:
        self.config = config
        self.token_count: int = 0
        self.compaction_threshold: float = compaction_threshold
        self.pruning_threshold: float = pruning_threshold
        self.keep_last: int = keep_last

    # ------------------------------------------------------------------ #
    #  Token tracking                                                      #
    # ------------------------------------------------------------------ #

    def update_token_count(self, usage: TokenUsage) -> None:
        """Update the current token count from LLM usage stats.

        ``usage.prompt_tokens`` reflects the number of tokens the model
        actually saw, so it is the best proxy for current context size.
        """
        self.token_count = usage.prompt_tokens
        logger.debug(
            "Context token count updated: %d / %d (%.1f%%)",
            self.token_count,
            self.config.context_window,
            self._usage_percent(),
        )

    # ------------------------------------------------------------------ #
    #  Threshold checks                                                    #
    # ------------------------------------------------------------------ #

    def needs_compaction(self) -> bool:
        """Return ``True`` if the context exceeds the compaction threshold."""
        return self.token_count > self.compaction_threshold * self.config.context_window

    def needs_pruning(self) -> bool:
        """Return ``True`` if the context exceeds the hard-pruning threshold."""
        return self.token_count > self.pruning_threshold * self.config.context_window

    # ------------------------------------------------------------------ #
    #  Token estimation                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def estimate_message_tokens(message: dict[str, Any]) -> int:
        """Rough estimate of the token count for a single message.

        Uses a simple heuristic: 1 token ≈ 4 characters, plus 10 tokens
        of overhead for role / formatting metadata.  This is deliberately
        approximate — good enough for pruning decisions without requiring
        a tokenizer dependency.
        """
        content = str(message.get("content", ""))
        return len(content) // 4 + 10

    # ------------------------------------------------------------------ #
    #  Pruning                                                             #
    # ------------------------------------------------------------------ #

    def prune_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return a pruned copy of *messages* that fits the context budget.

        Strategy
        --------
        1. The system message (index 0) is always kept.
        2. The last ``keep_last`` messages are always kept.
        3. Among the remaining "middle" messages, tool-result messages
           (``role == "tool"``) are removed first — they tend to be the
           largest.  Then old assistant messages are removed.
        4. Removal continues until the estimated total drops below the
           compaction threshold, or there is nothing left to remove.
        """
        if len(messages) <= 1 + self.keep_last:
            logger.debug("Too few messages to prune (%d) — returning as-is.", len(messages))
            return list(messages)

        # Partition: system | middle | tail
        system = messages[:1]
        tail = messages[-self.keep_last :]
        middle = messages[1 : -self.keep_last]

        target_tokens = int(self.compaction_threshold * self.config.context_window)

        def _total_estimate(msgs: list[dict[str, Any]]) -> int:
            return sum(self.estimate_message_tokens(m) for m in msgs)

        # First pass: remove tool-result messages from the middle.
        kept_middle: list[dict[str, Any]] = []
        for msg in middle:
            if msg.get("role") == "tool":
                logger.debug("Pruning tool message (call_id=%s).", msg.get("tool_call_id", "?"))
                continue
            kept_middle.append(msg)

        current = _total_estimate(system + kept_middle + tail)
        if current <= target_tokens:
            logger.debug(
                "Pruning complete after removing tool results (%d tokens est.).",
                current,
            )
            return system + kept_middle + tail

        # Second pass: remove old assistant messages from the front.
        pruned_middle: list[dict[str, Any]] = []
        for msg in reversed(kept_middle):
            candidate = system + [msg] + pruned_middle + tail
            if _total_estimate(candidate) <= target_tokens:
                pruned_middle.insert(0, msg)
                # Include all remaining older messages — they fit.
                idx = kept_middle.index(msg)
                pruned_middle = kept_middle[:idx] + pruned_middle
                break
            if msg.get("role") == "assistant":
                logger.debug("Pruning old assistant message.")
                continue
            pruned_middle.insert(0, msg)

        result = system + pruned_middle + tail
        logger.debug(
            "Pruning finished: %d -> %d messages (~%d tokens est.).",
            len(messages),
            len(result),
            _total_estimate(result),
        )
        return result

    # ------------------------------------------------------------------ #
    #  Stats                                                               #
    # ------------------------------------------------------------------ #

    def get_context_stats(self) -> dict[str, Any]:
        """Return a snapshot of context-window usage."""
        return {
            "token_count": self.token_count,
            "context_window": self.config.context_window,
            "usage_percent": round(self._usage_percent(), 2),
            "needs_compaction": self.needs_compaction(),
            "needs_pruning": self.needs_pruning(),
        }

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _usage_percent(self) -> float:
        """Context usage as a percentage (0–100)."""
        window = self.config.context_window
        if window <= 0:
            return 0.0
        return (self.token_count / window) * 100.0
