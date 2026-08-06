"""Safe planning helpers for reversible modem-configuration experiments."""

from __future__ import annotations

import re

from campnet.radio import ModemPreference

_WRITE_KEYS = {
    "mode_pref": "mode_pref",
    "rat_order_pref": "rat_acq_order",
    "lte_band": "lte_band",
    "nsa_nr5g_band": "nsa_nr5g_band",
    "nr5g_band": "nr5g_band",
    "nr5g_disable_mode": "nr5g_disable_mode",
}
_SAFE_VALUE = re.compile(r"^[A-Za-z0-9:]+$")


def build_restore_commands(preferences: tuple[ModemPreference, ...]) -> tuple[str, ...]:
    """Construct commands only; execution requires a separate explicit action."""

    commands: list[str] = []
    for preference in preferences:
        write_key = _WRITE_KEYS.get(preference.name)
        if write_key is None:
            continue
        if not _SAFE_VALUE.fullmatch(preference.value):
            raise ValueError(f"unsafe modem preference value for {preference.name}")
        commands.append(f'AT+QNWPREFCFG="{write_key}",{preference.value}')
    return tuple(commands)
