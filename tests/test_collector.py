from __future__ import annotations

from campnet.collector import SurveyCollector
from campnet.models import ProviderResult, SurveyMetadata, utc_now
from campnet.providers.base import CollectionContext


class GoodProvider:
    @property
    def name(self) -> str:
        return "good"

    def collect(self, context: CollectionContext) -> ProviderResult:
        return ProviderResult(
            provider=self.name,
            collected_at=utc_now(),
            data={"campground": context.metadata.campground},
            raw_responses={"example": "OK"},
        )


class BrokenProvider:
    @property
    def name(self) -> str:
        return "broken"

    def collect(self, context: CollectionContext) -> ProviderResult:
        del context
        raise RuntimeError("modem unavailable")


def test_collector_preserves_success_when_another_provider_fails() -> None:
    survey = SurveyCollector([GoodProvider(), BrokenProvider()]).collect(
        SurveyMetadata(campground="Test Camp")
    )

    assert len(survey.provider_results) == 2
    assert survey.provider_results[0].succeeded
    assert survey.provider_results[0].raw_responses == {"example": "OK"}
    assert not survey.provider_results[1].succeeded
    assert survey.provider_results[1].errors == ("RuntimeError: modem unavailable",)
