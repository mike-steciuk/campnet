"""Protocol-independent modem transport boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ATTransportResult:
    response: str
    raw_evidence: dict[str, str] = field(default_factory=dict)


class ATTransport(Protocol):
    """Exchange one AT command without interpreting its response."""

    def exchange(
        self, command: str, timeout_seconds: float
    ) -> str | ATTransportResult: ...
