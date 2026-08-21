from __future__ import annotations

from pathlib import Path

from campnet.at import ATClient
from campnet.execution import ExecutionEvidence, ExecutionFailure
from campnet.models import SurveyMetadata
from campnet.providers.at import ATProvider
from campnet.providers.base import CollectionContext
from campnet.transports import ReplayTransport


def test_at_provider_captures_fixture_responses() -> None:
    fixture = Path(__file__).parent / "fixtures" / "quectel_basic.json"
    provider = ATProvider(ATClient(ReplayTransport.from_json(fixture), retries=0))

    result = provider.collect(CollectionContext(metadata=SurveyMetadata()))

    assert result.succeeded
    assert set(result.raw_responses) == {
        "ATI#1",
        "AT+QNWINFO#1",
        'AT+QENG="servingcell"#1',
        'AT+QENG="neighbourcell"#1',
        "AT+QCAINFO#1",
    }
    assert "RM520N-GL" in result.raw_responses["ATI#1"]


def test_at_provider_preserves_failed_transport_evidence() -> None:
    class FailingTransport:
        def exchange(self, command: str, timeout_seconds: float) -> str:
            del command, timeout_seconds
            raise ExecutionFailure(
                "remote command failed",
                ExecutionEvidence(stdout="partial", stderr="failure", exit_code=9),
            )

    provider = ATProvider(ATClient(FailingTransport(), retries=0))

    result = provider.collect(CollectionContext(metadata=SurveyMetadata()))

    assert result.errors
    assert any(value == "partial" for value in result.raw_responses.values())
    assert any(value == "failure" for value in result.raw_responses.values())
    assert any('"exit_code": 9' in value for value in result.raw_responses.values())
