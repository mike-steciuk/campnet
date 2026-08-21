from __future__ import annotations

from collections import defaultdict, deque

from campnet.at import ATClient
from campnet.models import SurveyMetadata
from campnet.providers.base import CollectionContext
from campnet.providers.gnss import GNSSProvider


class GNSSSequenceTransport:
    def __init__(self) -> None:
        self.responses: dict[str, deque[str]] = defaultdict(deque)
        self.commands: list[str] = []

    def exchange(self, command: str, timeout_seconds: float) -> str:
        del timeout_seconds
        self.commands.append(command)
        return self.responses[command].popleft()


def test_gnss_provider_temporarily_enables_and_restores_gps() -> None:
    transport = GNSSSequenceTransport()
    transport.responses["AT+QGPS?"].append("+QGPS: 0\nOK\n")
    transport.responses["AT+QGPS=1"].append("OK\n")
    transport.responses["AT+QGPSLOC=2"].extend(
        [
            "+CME ERROR: 516\n",
            "+QGPSLOC: 120000.0,42.123,-83.456,0.8,250.0,3,180.0,1.2,0.6,050826,12\nOK\n",
        ]
    )
    transport.responses["AT+QGPSEND"].append("OK\n")
    provider = GNSSProvider(
        ATClient(transport, retries=0),
        enable_if_needed=True,
        fix_attempts=2,
        fix_interval_seconds=0,
        sleeper=lambda seconds: None,
    )

    result = provider.collect(CollectionContext(metadata=SurveyMetadata()))

    location = result.data["location"]
    assert isinstance(location, dict)
    assert location["latitude"] == 42.123
    assert location["longitude"] == -83.456
    assert result.data["temporarily_enabled"] is True
    assert transport.commands[-1] == "AT+QGPSEND"


def test_continuous_gnss_does_not_enable_disabled_receiver() -> None:
    transport = GNSSSequenceTransport()
    transport.responses["AT+QGPS?"].append("+QGPS: 0\nOK\n")
    provider = GNSSProvider(ATClient(transport, retries=0), enable_if_needed=False)

    result = provider.collect(CollectionContext(metadata=SurveyMetadata()))

    assert transport.commands == ["AT+QGPS?"]
    assert result.data["location"] == {}
    assert "does not change modem state" in result.errors[0]


def test_continuous_gnss_reads_existing_fix_once_without_state_change() -> None:
    transport = GNSSSequenceTransport()
    transport.responses["AT+QGPS?"].append("+QGPS: 1\nOK\n")
    transport.responses["AT+QGPSLOC=2"].append(
        "+QGPSLOC: 120000.0,42.123,-83.456,0.8,250.0,3,180.0,1.2,0.6,050826,12\nOK\n"
    )
    provider = GNSSProvider(
        ATClient(transport, retries=0),
        enable_if_needed=False,
        fix_attempts=1,
        report_unavailable_as_error=False,
    )

    result = provider.collect(CollectionContext(metadata=SurveyMetadata()))

    assert result.succeeded
    assert transport.commands == ["AT+QGPS?", "AT+QGPSLOC=2"]
    location = result.data["location"]
    assert isinstance(location, dict)
    assert location["latitude"] == 42.123
    assert result.data["temporarily_enabled"] is False
