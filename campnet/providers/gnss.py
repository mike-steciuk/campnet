"""Optional GNSS provider with reversible modem-state handling."""

from __future__ import annotations

import csv
import time
from collections.abc import Callable

from campnet.at import ATClient, ATExchange
from campnet.models import JsonValue, ProviderResult, utc_now
from campnet.providers.base import CollectionContext


class GNSSProvider:
    def __init__(
        self,
        client: ATClient,
        *,
        enable_if_needed: bool,
        fix_attempts: int = 6,
        fix_interval_seconds: float = 5.0,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self._enable_if_needed = enable_if_needed
        self._fix_attempts = fix_attempts
        self._fix_interval_seconds = fix_interval_seconds
        self._sleeper = sleeper

    @property
    def name(self) -> str:
        return "gnss"

    def collect(self, context: CollectionContext) -> ProviderResult:
        del context
        raw: dict[str, str] = {}
        errors: list[str] = []
        state = self._client.execute("AT+QGPS?")
        _record(state, raw, errors)
        initially_enabled = _gps_enabled(state.response or "")
        enabled_by_campnet = False
        location: dict[str, JsonValue] = {}
        try:
            if not initially_enabled and self._enable_if_needed:
                enable = self._client.execute("AT+QGPS=1", timeout_seconds=30.0)
                _record(enable, raw, errors)
                enabled_by_campnet = _modem_ok(enable.response or "")
            if initially_enabled or enabled_by_campnet:
                for attempt_number in range(self._fix_attempts):
                    fix = self._client.execute("AT+QGPSLOC=2", timeout_seconds=15.0)
                    _record(fix, raw, errors, key_suffix=f"fix{attempt_number + 1}")
                    location = _parse_location(fix.response or "")
                    if location:
                        break
                    if attempt_number + 1 < self._fix_attempts:
                        self._sleeper(self._fix_interval_seconds)
            elif not self._enable_if_needed:
                errors.append("GNSS is disabled; continuous profile does not change modem state")
        finally:
            if enabled_by_campnet:
                stop = self._client.execute("AT+QGPSEND", timeout_seconds=15.0)
                _record(stop, raw, errors)
        if not location and (initially_enabled or enabled_by_campnet):
            errors.append("GNSS did not acquire a location fix during the collection window")
        return ProviderResult(
            provider=self.name,
            collected_at=utc_now(),
            data={
                "initially_enabled": initially_enabled,
                "temporarily_enabled": enabled_by_campnet,
                "location": location,
            },
            raw_responses=raw,
            errors=tuple(errors),
        )


def _record(
    exchange: ATExchange,
    raw: dict[str, str],
    errors: list[str],
    *,
    key_suffix: str | None = None,
) -> None:
    for attempt in exchange.attempts:
        suffix = key_suffix or str(attempt.attempt)
        key = f"{exchange.command}#{suffix}"
        if attempt.response is not None:
            raw[key] = attempt.response
        if attempt.error is not None:
            errors.append(f"{key}: {attempt.error}")


def _gps_enabled(response: str) -> bool:
    return any(line.strip() == "+QGPS: 1" for line in response.splitlines())


def _modem_ok(response: str) -> bool:
    return any(line.strip() == "OK" for line in response.splitlines())


def _parse_location(response: str) -> dict[str, JsonValue]:
    line = next((line.strip() for line in response.splitlines() if "+QGPSLOC:" in line), None)
    if line is None:
        return {}
    fields = next(csv.reader([line.split(":", 1)[1]], skipinitialspace=True))
    if len(fields) < 6:
        return {}
    return {
        "utc": fields[0],
        "latitude": _float(fields[1]),
        "longitude": _float(fields[2]),
        "hdop": _float(fields[3]),
        "altitude_m": _float(fields[4]),
        "fix_type": _integer(fields[5]),
        "course_degrees": _float(fields[6]) if len(fields) > 6 else None,
        "speed_kph": _float(fields[7]) if len(fields) > 7 else None,
        "speed_knots": _float(fields[8]) if len(fields) > 8 else None,
        "date": fields[9] if len(fields) > 9 else None,
        "satellites": _integer(fields[10]) if len(fields) > 10 else None,
    }


def _float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def _integer(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
