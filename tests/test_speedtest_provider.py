from __future__ import annotations

from campnet.models import JsonValue, SurveyMetadata
from campnet.providers.base import CollectionContext
from campnet.providers.speedtest import SpeedTestProvider


class FakeSpeedTestAdapter:
    @property
    def name(self) -> str:
        return "fake-speedtest"

    @property
    def execution_scope(self) -> str:
        return "collector_host"

    def run(self, timeout_seconds: float) -> tuple[dict[str, JsonValue], str]:
        assert timeout_seconds == 30.0
        return (
            {
                "download_mbps": 47.25,
                "upload_mbps": 8.5,
                "latency_ms": 31.2,
                "jitter_ms": 2.1,
                "packet_loss_percent": 0.0,
                "isp": "Example ISP",
                "server_name": "Example Server",
            },
            '{"raw":true}',
        )


class FailingRouterAdapter:
    @property
    def name(self) -> str:
        return "speedtest-cli"

    @property
    def execution_scope(self) -> str:
        return "router"

    def run(self, timeout_seconds: float) -> tuple[dict[str, JsonValue], str]:
        del timeout_seconds
        raise RuntimeError("HTTP Error 429")


def test_speedtest_provider_normalizes_and_preserves_raw_output() -> None:
    provider = SpeedTestProvider(FakeSpeedTestAdapter(), timeout_seconds=30.0)

    result = provider.collect(CollectionContext(metadata=SurveyMetadata()))

    assert result.succeeded
    assert result.data["download_mbps"] == 47.25
    assert result.data["tool"] == "fake-speedtest"
    assert result.data["execution_scope"] == "collector_host"
    assert result.raw_responses == {"result.json": '{"raw":true}'}


def test_speedtest_provider_records_router_fallback_reason() -> None:
    provider = SpeedTestProvider(
        FailingRouterAdapter(),
        fallback_adapter=FakeSpeedTestAdapter(),
        timeout_seconds=30.0,
    )

    result = provider.collect(CollectionContext(metadata=SurveyMetadata()))

    assert result.succeeded
    assert result.data["execution_scope"] == "collector_host"
    assert result.data["fallback_used"] is True
    assert result.data["fallback_reason"] == "router: RuntimeError: HTTP Error 429"
