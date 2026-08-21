"""Normalize provider-specific evidence at collection and schema-read boundaries."""

from __future__ import annotations

from dataclasses import replace

from campnet.models import JsonValue, ProviderResult, Survey
from campnet.parsers import parse_quectel_snapshot
from campnet.radio import radio_snapshot_to_dict


def normalize_at_result(result: ProviderResult) -> ProviderResult:
    if result.provider != "at":
        return result
    data = dict(result.data)
    if "radio" not in data:
        data["radio"] = radio_snapshot_to_dict(parse_quectel_snapshot(result.raw_responses))
    multi_sim = data.get("multi_sim")
    if isinstance(multi_sim, dict):
        normalized_multi_sim = dict(multi_sim)
        segments = multi_sim.get("segments")
        if isinstance(segments, list):
            normalized_segments: list[JsonValue] = []
            for segment in segments:
                if not isinstance(segment, dict):
                    normalized_segments.append(segment)
                    continue
                normalized_segment = dict(segment)
                nested = segment.get("at_result")
                if isinstance(nested, dict):
                    nested_result = ProviderResult.from_dict(nested)
                    normalized_segment["at_result"] = normalize_at_result(nested_result).to_dict()
                normalized_segments.append(normalized_segment)
            normalized_multi_sim["segments"] = normalized_segments
        data["multi_sim"] = normalized_multi_sim
    return replace(result, data=data)


def normalize_survey(survey: Survey) -> Survey:
    return replace(
        survey,
        provider_results=tuple(normalize_at_result(result) for result in survey.provider_results),
    )
