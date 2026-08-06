"""Versioned canonical models shared by providers, analysis, and reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TypeAlias, cast

APP_VERSION = "0.1.0"
SCHEMA_VERSION = 1

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def utc_now() -> datetime:
    return datetime.now(UTC)


def datetime_to_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("timestamps must include timezone information")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def datetime_from_text(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include timezone information")
    return parsed.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class SurveyMetadata:
    campground: str | None = None
    site: str | None = None
    notes: str | None = None
    router_placement: str | None = None
    antenna_configuration: str | None = None

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "campground": self.campground,
            "site": self.site,
            "notes": self.notes,
            "router_placement": self.router_placement,
            "antenna_configuration": self.antenna_configuration,
        }

    @classmethod
    def from_dict(cls, value: dict[str, JsonValue]) -> SurveyMetadata:
        return cls(
            campground=_optional_string(value.get("campground")),
            site=_optional_string(value.get("site")),
            notes=_optional_string(value.get("notes")),
            router_placement=_optional_string(value.get("router_placement")),
            antenna_configuration=_optional_string(value.get("antenna_configuration")),
        )


@dataclass(frozen=True, slots=True)
class ProviderResult:
    provider: str
    collected_at: datetime
    data: dict[str, JsonValue] = field(default_factory=dict)
    raw_responses: dict[str, str] = field(default_factory=dict)
    errors: tuple[str, ...] = ()

    @property
    def succeeded(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, JsonValue]:
        raw_responses: dict[str, JsonValue] = {
            key: response for key, response in self.raw_responses.items()
        }
        return {
            "provider": self.provider,
            "collected_at": datetime_to_text(self.collected_at),
            "data": self.data,
            "raw_responses": raw_responses,
            "errors": list(self.errors),
        }

    @classmethod
    def from_dict(cls, value: dict[str, JsonValue]) -> ProviderResult:
        provider = value.get("provider")
        collected_at = value.get("collected_at")
        data = value.get("data", {})
        raw = value.get("raw_responses", {})
        errors = value.get("errors", [])
        if not isinstance(provider, str) or not isinstance(collected_at, str):
            raise ValueError("provider result requires provider and collected_at strings")
        if not isinstance(data, dict) or not isinstance(raw, dict) or not isinstance(errors, list):
            raise ValueError("invalid provider result collections")
        if not all(isinstance(key, str) and isinstance(item, str) for key, item in raw.items()):
            raise ValueError("raw responses must map strings to strings")
        if not all(isinstance(item, str) for item in errors):
            raise ValueError("provider errors must be strings")
        return cls(
            provider=provider,
            collected_at=datetime_from_text(collected_at),
            data=data,
            raw_responses=cast(dict[str, str], raw),
            errors=tuple(cast(list[str], errors)),
        )


@dataclass(frozen=True, slots=True)
class Survey:
    timestamp: datetime
    metadata: SurveyMetadata
    provider_results: tuple[ProviderResult, ...] = ()
    recommendations: tuple[str, ...] = ()
    schema_version: int = SCHEMA_VERSION
    app_version: str = APP_VERSION

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schema_version": self.schema_version,
            "app_version": self.app_version,
            "timestamp": datetime_to_text(self.timestamp),
            "metadata": self.metadata.to_dict(),
            "provider_results": [result.to_dict() for result in self.provider_results],
            "recommendations": list(self.recommendations),
        }

    @classmethod
    def from_dict(cls, value: dict[str, JsonValue]) -> Survey:
        schema_version = value.get("schema_version")
        app_version = value.get("app_version")
        timestamp = value.get("timestamp")
        metadata = value.get("metadata")
        results = value.get("provider_results", [])
        recommendations = value.get("recommendations", [])
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported survey schema version: {schema_version!r}")
        if not isinstance(app_version, str) or not isinstance(timestamp, str):
            raise ValueError("survey requires app_version and timestamp strings")
        if not isinstance(metadata, dict) or not isinstance(results, list):
            raise ValueError("invalid survey metadata or provider results")
        if not isinstance(recommendations, list) or not all(
            isinstance(item, str) for item in recommendations
        ):
            raise ValueError("recommendations must be strings")
        return cls(
            timestamp=datetime_from_text(timestamp),
            metadata=SurveyMetadata.from_dict(metadata),
            provider_results=tuple(
                ProviderResult.from_dict(item) for item in results if isinstance(item, dict)
            ),
            recommendations=tuple(cast(list[str], recommendations)),
            schema_version=SCHEMA_VERSION,
            app_version=app_version,
        )


def _optional_string(value: JsonValue | None) -> str | None:
    if value is None or isinstance(value, str):
        return value
    raise ValueError(f"expected a string or null, received {type(value).__name__}")
