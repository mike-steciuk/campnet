"""Protocol-independent modem transport boundary."""

from __future__ import annotations

from typing import Protocol


class ATTransport(Protocol):
    """Exchange one AT command without interpreting its response."""

    def exchange(self, command: str, timeout_seconds: float) -> str: ...
