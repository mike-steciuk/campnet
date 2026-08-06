"""Survey orchestration across independent providers."""

from __future__ import annotations

from collections.abc import Iterable

from campnet.models import ProviderResult, Survey, SurveyMetadata, utc_now
from campnet.providers import CollectionContext, DataProvider


class SurveyCollector:
    def __init__(self, providers: Iterable[DataProvider]) -> None:
        self._providers = tuple(providers)

    def collect(self, metadata: SurveyMetadata) -> Survey:
        context = CollectionContext(metadata=metadata)
        results: list[ProviderResult] = []
        for provider in self._providers:
            try:
                result = provider.collect(context)
                if result.provider != provider.name:
                    raise ValueError(
                        f"provider {provider.name!r} returned result for {result.provider!r}"
                    )
                results.append(result)
            except Exception as error:  # Providers are intentionally isolated.
                results.append(
                    ProviderResult(
                        provider=provider.name,
                        collected_at=utc_now(),
                        errors=(f"{type(error).__name__}: {error}",),
                    )
                )
        return Survey(timestamp=utc_now(), metadata=metadata, provider_results=tuple(results))
