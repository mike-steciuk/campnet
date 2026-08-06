"""Deterministic transport for captured modem-response fixtures."""

from __future__ import annotations

import json
from pathlib import Path


class ReplayTransport:
    def __init__(self, responses: dict[str, str]) -> None:
        self._responses = dict(responses)

    @classmethod
    def from_json(cls, path: Path) -> ReplayTransport:
        value: object = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or not all(
            isinstance(command, str) and isinstance(response, str)
            for command, response in value.items()
        ):
            raise ValueError("AT fixture must be a JSON object mapping commands to responses")
        return cls(value)

    def exchange(self, command: str, timeout_seconds: float) -> str:
        del timeout_seconds
        try:
            return self._responses[command]
        except KeyError as error:
            raise LookupError(f"fixture has no response for {command}") from error
