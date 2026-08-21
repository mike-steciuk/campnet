from __future__ import annotations

from campnet.execution import ExecutionEvidence, ExecutionFailure
from campnet.models import SurveyMetadata
from campnet.providers.base import CollectionContext
from campnet.providers.speedtest import SpeedTestProvider, SpeedTestRun


class FakeSpeedTestAdapter:
    @property
    def name(self) -> str:
        return "fake-speedtest"

    @property
    def execution_scope(self) -> str:
        return "collector_host"

    def run(self, timeout_seconds: float) -> SpeedTestRun:
        assert timeout_seconds == 30.0
        return SpeedTestRun(
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
            ExecutionEvidence(stdout='{"raw":true}', exit_code=0),
        )


class FailingRouterAdapter:
    @property
    def name(self) -> str:
        return "speedtest-cli"

    @property
    def execution_scope(self) -> str:
        return "router"

    def run(self, timeout_seconds: float) -> SpeedTestRun:
        del timeout_seconds
        raise ExecutionFailure(
            "HTTP Error 429",
            ExecutionEvidence(stdout="partial output", stderr="HTTP 429", exit_code=1),
        )


def test_speedtest_provider_normalizes_and_preserves_raw_output() -> None:
    provider = SpeedTestProvider(FakeSpeedTestAdapter(), timeout_seconds=30.0)

    result = provider.collect(CollectionContext(metadata=SurveyMetadata()))

    assert result.succeeded
    assert result.data["download_mbps"] == 47.25
    assert result.data["tool"] == "fake-speedtest"
    assert result.data["execution_scope"] == "collector_host"
    assert result.raw_responses["result.json"] == '{"raw":true}'
    assert result.raw_responses["attempt-1-collector_host.stdout"] == '{"raw":true}'
    assert '"exit_code": 0' in result.raw_responses[
        "attempt-1-collector_host.execution.json"
    ]


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
    assert result.data["fallback_reason"] == "router: ExecutionFailure: HTTP Error 429"
    assert result.raw_responses["attempt-1-router.stdout"] == "partial output"
    assert result.raw_responses["attempt-1-router.stderr"] == "HTTP 429"
    assert '"exit_code": 1' in result.raw_responses["attempt-1-router.execution.json"]
