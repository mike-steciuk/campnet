from __future__ import annotations

from pathlib import Path

from campnet.at import ATClient
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
