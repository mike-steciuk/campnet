"""Retrying AT client that preserves every modem response."""

from __future__ import annotations

from dataclasses import dataclass

from campnet.transports import ATTransport


@dataclass(frozen=True, slots=True)
class ATAttempt:
    command: str
    attempt: int
    response: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ATExchange:
    command: str
    attempts: tuple[ATAttempt, ...]

    @property
    def response(self) -> str | None:
        return self.attempts[-1].response if self.attempts else None

    @property
    def succeeded(self) -> bool:
        return self.response is not None


class ATClient:
    def __init__(
        self,
        transport: ATTransport,
        *,
        retries: int = 1,
        timeout_seconds: float = 10.0,
    ) -> None:
        if retries < 0:
            raise ValueError("retries cannot be negative")
        if timeout_seconds <= 0:
            raise ValueError("timeout must be positive")
        self._transport = transport
        self._retries = retries
        self._timeout_seconds = timeout_seconds

    def execute(self, command: str, *, timeout_seconds: float | None = None) -> ATExchange:
        normalized = command.strip()
        if not normalized.upper().startswith("AT"):
            raise ValueError("AT commands must begin with AT")
        attempts: list[ATAttempt] = []
        timeout = timeout_seconds if timeout_seconds is not None else self._timeout_seconds
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        for attempt_number in range(1, self._retries + 2):
            try:
                response = self._transport.exchange(normalized, timeout)
                attempts.append(
                    ATAttempt(command=normalized, attempt=attempt_number, response=response)
                )
                return ATExchange(command=normalized, attempts=tuple(attempts))
            except Exception as error:  # Transport implementations define concrete failures.
                attempts.append(
                    ATAttempt(
                        command=normalized,
                        attempt=attempt_number,
                        error=f"{type(error).__name__}: {error}",
                    )
                )
        return ATExchange(command=normalized, attempts=tuple(attempts))
