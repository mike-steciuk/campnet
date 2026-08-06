"""Provider contract for independent survey data sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from campnet.models import ProviderResult, SurveyMetadata


@dataclass(frozen=True, slots=True)
class CollectionContext:
    metadata: SurveyMetadata


class DataProvider(Protocol):
    """A source that contributes observations without owning the Survey model."""

    @property
    def name(self) -> str: ...

    def collect(self, context: CollectionContext) -> ProviderResult: ...
