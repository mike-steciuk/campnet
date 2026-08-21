from __future__ import annotations

from collections import deque

from campnet.at import ATClient
from campnet.transports import ATTransportResult


class SequenceTransport:
    def __init__(self, outcomes: list[str | Exception]) -> None:
        self.outcomes = deque(outcomes)

    def exchange(self, command: str, timeout_seconds: float) -> str:
        assert command == "ATI"
        assert timeout_seconds == 2.0
        outcome = self.outcomes.popleft()
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_at_client_retries_and_preserves_failed_attempt() -> None:
    client = ATClient(
        SequenceTransport([TimeoutError("slow modem"), "RM520N\r\nOK\r\n"]),
        retries=1,
        timeout_seconds=2.0,
    )

    exchange = client.execute(" ATI ")

    assert exchange.succeeded
    assert len(exchange.attempts) == 2
    assert exchange.attempts[0].error == "TimeoutError: slow modem"
    assert exchange.response == "RM520N\r\nOK\r\n"


def test_at_client_rejects_non_at_commands() -> None:
    client = ATClient(SequenceTransport([]))

    try:
        client.execute("reboot")
    except ValueError as error:
        assert "begin with AT" in str(error)
    else:
        raise AssertionError("unsafe non-AT command was accepted")


def test_at_client_preserves_successful_transport_evidence() -> None:
    class EvidenceTransport:
        def exchange(self, command: str, timeout_seconds: float) -> ATTransportResult:
            del command, timeout_seconds
            return ATTransportResult(
                "OK\n",
                {"ssh.execution.json": '{"exit_code": 0}', "ssh.stderr": "warning"},
            )

    exchange = ATClient(EvidenceTransport(), retries=0).execute("ATI")

    assert exchange.attempts[0].raw_evidence == {
        "ssh.execution.json": '{"exit_code": 0}',
        "ssh.stderr": "warning",
    }
