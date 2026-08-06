"""Safe provider that records the host environment running CampNet."""

from __future__ import annotations

import platform

from campnet.models import ProviderResult, utc_now
from campnet.providers.base import CollectionContext


class SystemProvider:
    @property
    def name(self) -> str:
        return "system"

    def collect(self, context: CollectionContext) -> ProviderResult:
        del context
        return ProviderResult(
            provider=self.name,
            collected_at=utc_now(),
            data={
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "python_version": platform.python_version(),
            },
        )
