from __future__ import annotations

from campnet.configuration import build_restore_commands
from campnet.radio import ModemPreference


def test_build_restore_commands_maps_response_names_to_write_keys() -> None:
    preferences = (
        ModemPreference(query='AT+QNWPREFCFG="mode_pref"', name="mode_pref", value="AUTO"),
        ModemPreference(
            query='AT+QNWPREFCFG="rat_acq_order"',
            name="rat_order_pref",
            value="NR5G:LTE:WCDMA",
        ),
        ModemPreference(query='AT+QNWPREFCFG="lte_band"', name="lte_band", value="2:12:14"),
    )

    assert build_restore_commands(preferences) == (
        'AT+QNWPREFCFG="mode_pref",AUTO',
        'AT+QNWPREFCFG="rat_acq_order",NR5G:LTE:WCDMA',
        'AT+QNWPREFCFG="lte_band",2:12:14',
    )


def test_restore_plan_rejects_unexpected_characters() -> None:
    preferences = (
        ModemPreference(query='AT+QNWPREFCFG="lte_band"', name="lte_band", value="2;AT+CFUN=0"),
    )

    try:
        build_restore_commands(preferences)
    except ValueError as error:
        assert "unsafe modem preference" in str(error)
    else:
        raise AssertionError("unsafe restore value was accepted")
