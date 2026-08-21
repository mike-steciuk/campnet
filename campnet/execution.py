"""Structured raw evidence for external command executions."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionEvidence:
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    timed_out: bool = False

    def raw_responses(self, prefix: str) -> dict[str, str]:
        raw = {
            f"{prefix}.execution.json": json.dumps(
                {"exit_code": self.exit_code, "timed_out": self.timed_out},
                sort_keys=True,
            )
        }
        if self.stdout:
            raw[f"{prefix}.stdout"] = self.stdout
        if self.stderr:
            raw[f"{prefix}.stderr"] = self.stderr
        return raw


class ExecutionFailure(RuntimeError):
    def __init__(self, message: str, evidence: ExecutionEvidence) -> None:
        super().__init__(message)
        self.evidence = evidence


def timeout_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value or ""
