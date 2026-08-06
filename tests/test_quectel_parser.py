from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from campnet.parsers import parse_quectel_snapshot


def test_parse_observed_quectel_response_shapes() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "quectel_basic.json"
    fixture = cast(dict[str, str], json.loads(fixture_path.read_text(encoding="utf-8")))
    raw = {f"{command}#1": response for command, response in fixture.items()}

    snapshot = parse_quectel_snapshot(raw)

    assert snapshot.modem is not None
    assert snapshot.modem.model == "RM520N-GL"
    assert snapshot.networks[0].plmn == "310410"
    assert snapshot.networks[0].band == "LTE BAND 2"
    assert snapshot.serving_cells[0].band == "LTE BAND 2"
    assert snapshot.serving_cells[0].rsrp_dbm == -108
    assert snapshot.serving_cells[1].band == "NR5G BAND 5"
    assert snapshot.serving_cells[1].sinr_db == 3
    assert len(snapshot.neighbor_cells) == 2
    assert snapshot.carrier_components[0].role == "PCC"


def test_parse_extended_carrier_scan() -> None:
    raw = {
        "AT+COPS=?#1": (
            '+COPS: (1,"AT&T","AT&T","310410",7),(1,"Verizon","Verizon","311480",7)\nOK\n'
        ),
        "AT+QSCAN=1#1": (
            '+QSCAN: "LTE",310,410,1125,250,-108,-13,18,111\n'
            '+QSCAN: "LTE",311,480,5230,207,-94,-13,34,113\nOK\n'
        ),
    }

    snapshot = parse_quectel_snapshot(raw)

    assert [operator.name for operator in snapshot.operators] == ["AT&T", "Verizon"]
    assert snapshot.visible_cells[0].band == "LTE BAND 2"
    assert snapshot.visible_cells[1].band == "LTE BAND 13"
    assert snapshot.visible_cells[1].rsrp_dbm == -94


def test_parse_modem_preferences_for_restore_baseline() -> None:
    raw = {
        'AT+QNWPREFCFG="mode_pref"#1': ('+QNWPREFCFG: "mode_pref",AUTO\nOK\n'),
        'AT+QNWPREFCFG="rat_acq_order"#1': ('+QNWPREFCFG: "rat_order_pref",NR5G:LTE\nOK\n'),
        'AT+QNWPREFCFG="lte_band"#1': ('+QNWPREFCFG: "lte_band",2:5:12:14:66\nOK\n'),
    }

    snapshot = parse_quectel_snapshot(raw)

    assert [(item.name, item.value) for item in snapshot.modem_preferences] == [
        ("mode_pref", "AUTO"),
        ("rat_order_pref", "NR5G:LTE"),
        ("lte_band", "2:5:12:14:66"),
    ]
