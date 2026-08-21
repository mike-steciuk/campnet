"""Safe planning helpers for reversible modem-configuration experiments."""

from __future__ import annotations

import re
from dataclasses import dataclass

from campnet.at_registry import command
from campnet.radio import ModemPreference

_WRITE_KEYS = {
    "mode_pref": "config.set_mode_preference",
    "rat_order_pref": "config.set_rat_order",
    "lte_band": "config.set_lte_bands",
    "nsa_nr5g_band": "config.set_nsa_bands",
    "nr5g_band": "config.set_sa_bands",
    "nr5g_disable_mode": "config.set_nr_mode",
}
_SAFE_VALUE = re.compile(r"^[A-Za-z0-9:]+$")


@dataclass(frozen=True, slots=True)
class PlannedATOperation:
    command_id: str
    parameters: tuple[tuple[str, str], ...]

    def render(self) -> str:
        return command(self.command_id).render(**dict(self.parameters))


def build_restore_plan(preferences: tuple[ModemPreference, ...]) -> tuple[PlannedATOperation, ...]:
    """Plan registry operations only; execution requires explicit authorization."""

    operations: list[PlannedATOperation] = []
    for preference in preferences:
        command_id = _WRITE_KEYS.get(preference.name)
        if command_id is None:
            continue
        if not _SAFE_VALUE.fullmatch(preference.value):
            raise ValueError(f"unsafe modem preference value for {preference.name}")
        operations.append(PlannedATOperation(command_id, (("value", preference.value),)))
    return tuple(operations)
