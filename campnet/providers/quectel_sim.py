"""Quectel AT implementation of the hardware-neutral SIM-slot contract."""

from __future__ import annotations

import re
import time
from collections.abc import Callable

from campnet.at import ATClient, ATExchange
from campnet.at_registry import command, require_authorization
from campnet.sim import SIMInventory, SIMSelection, SIMState


class QuectelATSimSlotController:
    """Discover, select, verify, and await SIM slots using Quectel AT commands."""

    def __init__(
        self,
        client: ATClient,
        *,
        registration_attempts: int = 12,
        registration_interval_seconds: float = 10.0,
        sleeper: Callable[[float], None] = time.sleep,
        authorized: bool = False,
    ) -> None:
        self._client = client
        self._registration_attempts = registration_attempts
        self._registration_interval_seconds = registration_interval_seconds
        self._sleeper = sleeper
        self._authorized = authorized

    def inventory(self) -> SIMInventory:
        raw: dict[str, str] = {}
        errors: list[str] = []
        active = self._client.execute(command("sim.active_slot").render())
        _record_exchange(active, raw, errors, prefix="inventory")
        status = self._client.execute(command("sim.dual_slot_status").render())
        _record_exchange(status, raw, errors, prefix="inventory")
        return SIMInventory(
            active_slot=parse_active_slot(active.response or ""),
            installed_slots=parse_installed_slots(status.response or ""),
            raw_responses=raw,
            errors=tuple(errors),
        )

    def state(self, slot: int | None) -> SIMState:
        return self._query_state(slot, prefix=f"slot{slot or 'unknown'}-state")

    def select(self, slot: int) -> SIMSelection:
        raw: dict[str, str] = {}
        errors: list[str] = []
        definition = command("sim.switch_slot")
        require_authorization(definition, authorized=self._authorized)
        switched = self._client.execute(
            definition.render(slot=str(slot)),
            timeout_seconds=definition.execution.recommended_timeout_seconds,
        )
        _record_exchange(switched, raw, errors, prefix=f"slot{slot}-select")
        if not _modem_ok(switched.response or ""):
            return SIMSelection(slot, False, raw, tuple(errors))
        verification = self._client.execute(command("sim.active_slot").render())
        _record_exchange(verification, raw, errors, prefix=f"slot{slot}-verify")
        selected = parse_active_slot(verification.response or "") == slot
        if not selected:
            errors.append(f"SIM slot verification failed: expected {slot}")
        return SIMSelection(slot, selected, raw, tuple(errors))

    def wait_until_ready(self, slot: int) -> SIMState:
        raw: dict[str, str] = {}
        errors: list[str] = []
        ready = False
        registered = False
        for attempt in range(1, self._registration_attempts + 1):
            state = self._query_state(slot, prefix=f"slot{slot}-wait{attempt}")
            raw.update(state.raw_responses)
            errors.extend(state.errors)
            ready, registered = state.ready, state.registered
            if ready and registered:
                break
            if attempt < self._registration_attempts:
                self._sleeper(self._registration_interval_seconds)
        if not (ready and registered):
            errors.append(f"SIM slot {slot} did not register within the collection window")
        return SIMState(slot, ready, registered, raw, tuple(errors))

    def _query_state(self, slot: int | None, *, prefix: str) -> SIMState:
        raw: dict[str, str] = {}
        errors: list[str] = []
        pin = self._client.execute(command("sim.readiness").render())
        registration = self._client.execute(command("network.eps_registration").render())
        _record_exchange(pin, raw, errors, prefix=prefix)
        _record_exchange(registration, raw, errors, prefix=prefix)
        return SIMState(
            slot,
            sim_ready(pin.response or ""),
            registration_ready(registration.response or ""),
            raw,
            tuple(errors),
        )


def parse_active_slot(response: str) -> int | None:
    match = re.search(r"\+QUIMSLOT:\s*([1-9][0-9]*)", response)
    return int(match.group(1)) if match else None


def parse_installed_slots(response: str) -> tuple[int, ...]:
    match = re.search(r'\+QSIMCFG:\s*"dual_slot_status"\s*,\s*([01])\s*,\s*([01])', response)
    if match is None:
        return ()
    return tuple(index for index, value in enumerate(match.groups(), start=1) if value == "1")


def sim_ready(response: str) -> bool:
    return bool(re.search(r"\+CPIN:\s*READY", response))


def registration_ready(response: str) -> bool:
    match = re.search(r"\+CEREG:\s*\d+\s*,\s*([0-9]+)", response)
    return match is not None and match.group(1) in {"1", "5"}


def _record_exchange(
    exchange: ATExchange, raw: dict[str, str], errors: list[str], *, prefix: str
) -> None:
    for attempt in exchange.attempts:
        key = f"{prefix}:{exchange.command}#{attempt.attempt}"
        if attempt.response is not None:
            raw[key] = attempt.response
        if attempt.raw_evidence is not None:
            raw.update({f"{key}:{name}": value for name, value in attempt.raw_evidence.items()})
        if attempt.error is not None:
            errors.append(f"{key}: {attempt.error}")


def _modem_ok(response: str) -> bool:
    return any(line.strip() == "OK" for line in response.splitlines())
