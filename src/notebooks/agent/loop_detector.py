"""Loop detection for the coding agent.

Detects when the agent is stuck in a loop — repeatedly making the same
tool calls or producing the same responses.  The detector tracks a rolling
window of action *signatures* (hashed action + params) and flags when
patterns repeat beyond a configurable threshold.
"""

from __future__ import annotations

import hashlib
import json


class LoopDetector:
    """Detects repetitive patterns in the agent's behavior.

    Parameters
    ----------
    max_repeats : int
        How many times a signature can repeat within the window before
        :meth:`is_looping` returns ``True``.
    window_size : int
        How many recent signatures to keep in the rolling buffer.
    """

    def __init__(self, max_repeats: int = 3, window_size: int = 10) -> None:
        self.max_repeats = max_repeats
        self.window_size = window_size
        self._signatures: list[str] = []

    # ------------------------------------------------------------------ #
    #  Recording                                                           #
    # ------------------------------------------------------------------ #

    def record(self, action: str, params: dict | None = None) -> None:
        """Record an action signature.

        The signature is an MD5 hex-digest of ``"{action}:{sorted_params}"``.
        Only the last :attr:`window_size` entries are retained.

        Parameters
        ----------
        action : str
            Name of the action (e.g. tool name or ``"text_response"``).
        params : dict | None
            Optional parameters associated with the action.
        """
        params_json = json.dumps(params, sort_keys=True) if params else ""
        raw = f"{action}:{params_json}"
        sig = hashlib.md5(raw.encode()).hexdigest()
        self._signatures.append(sig)
        # Keep only the most recent entries
        if len(self._signatures) > self.window_size:
            self._signatures = self._signatures[-self.window_size :]

    # ------------------------------------------------------------------ #
    #  Simple repeat detection                                             #
    # ------------------------------------------------------------------ #

    def is_looping(self) -> bool:
        """Return ``True`` if the most recent signature repeats too often.

        "Too often" means the latest signature appears at least
        :attr:`max_repeats` times within the current window.
        """
        if not self._signatures:
            return False
        latest = self._signatures[-1]
        count = self._signatures.count(latest)
        return count >= self.max_repeats

    # ------------------------------------------------------------------ #
    #  Cycle detection                                                     #
    # ------------------------------------------------------------------ #

    def detect_cycle(
        self,
        min_cycle_length: int = 2,
        max_cycle_length: int = 5,
    ) -> list[str] | None:
        """Look for a repeating cycle in the recent signatures.

        Checks whether the last *k* signatures (for *k* in
        ``[min_cycle_length, max_cycle_length]``) repeat at least twice
        consecutively at the tail of the window.

        Parameters
        ----------
        min_cycle_length : int
            Shortest cycle to search for.
        max_cycle_length : int
            Longest cycle to search for.

        Returns
        -------
        list[str] | None
            The repeating cycle (list of signature hashes) if one is
            found, otherwise ``None``.
        """
        n = len(self._signatures)
        for k in range(min_cycle_length, max_cycle_length + 1):
            # Need at least 2 full cycles to confirm repetition
            if n < 2 * k:
                continue
            cycle = self._signatures[-k:]
            preceding = self._signatures[-2 * k : -k]
            if cycle == preceding:
                return cycle
        return None

    # ------------------------------------------------------------------ #
    #  Diagnostic message                                                  #
    # ------------------------------------------------------------------ #

    def get_loop_message(self) -> str:
        """Return a diagnostic message to inject when a loop is detected.

        This message is intended to be appended to the conversation so the
        model is made aware it is repeating itself and should change
        strategy.
        """
        cycle = self.detect_cycle()
        if cycle is not None:
            return (
                "SYSTEM: Loop detected — you have been repeating the same "
                f"sequence of {len(cycle)} actions. Please stop and try a "
                "fundamentally different approach to solve the problem."
            )
        return (
            "SYSTEM: Loop detected — you are repeating the same action. "
            "Please stop and try a different approach. Consider:\n"
            "  1. Re-reading the relevant code or error message carefully.\n"
            "  2. Trying an alternative tool or strategy.\n"
            "  3. Asking the user for clarification."
        )

    # ------------------------------------------------------------------ #
    #  Reset                                                               #
    # ------------------------------------------------------------------ #

    def reset(self) -> None:
        """Clear all recorded signatures."""
        self._signatures = []
