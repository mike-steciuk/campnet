"""Conservative parsers for observed Quectel RM520N AT response formats."""

from __future__ import annotations

import csv
import re

from campnet.radio import (
    CarrierComponent,
    ModemInfo,
    ModemPreference,
    NetworkInfo,
    OperatorInfo,
    RadioCell,
    RadioSnapshot,
    VisibleCell,
)


def parse_quectel_snapshot(raw_responses: dict[str, str]) -> RadioSnapshot:
    return RadioSnapshot(
        modem=_parse_ati(_response(raw_responses, "ATI")),
        networks=tuple(_parse_qnwinfo(_response(raw_responses, "AT+QNWINFO"))),
        serving_cells=tuple(_parse_serving(_response(raw_responses, 'AT+QENG="servingcell"'))),
        neighbor_cells=tuple(_parse_neighbors(_response(raw_responses, 'AT+QENG="neighbourcell"'))),
        carrier_components=tuple(_parse_qcainfo(_response(raw_responses, "AT+QCAINFO"))),
        operators=tuple(_parse_cops(_response(raw_responses, "AT+COPS=?"))),
        visible_cells=tuple(_parse_qscan(_response(raw_responses, "AT+QSCAN=1"))),
        modem_preferences=tuple(_parse_preferences(raw_responses)),
    )


def _response(raw_responses: dict[str, str], command: str) -> str:
    pattern = re.compile(rf"^{re.escape(command)}#(\d+)$")
    candidates = sorted(
        (int(match.group(1)), key)
        for key in raw_responses
        if (match := pattern.fullmatch(key)) is not None
    )
    return raw_responses[candidates[-1][1]] if candidates else ""


def _parse_ati(response: str) -> ModemInfo | None:
    lines = _content_lines(response, prefix=None)
    if not lines:
        return None
    revision = next(
        (line.split(":", 1)[1].strip() for line in lines if line.startswith("Revision:")),
        None,
    )
    ordinary = [line for line in lines if not line.startswith("Revision:")]
    return ModemInfo(
        manufacturer=ordinary[0] if ordinary else None,
        model=ordinary[1] if len(ordinary) > 1 else None,
        revision=revision,
    )


def _parse_qnwinfo(response: str) -> list[NetworkInfo]:
    networks: list[NetworkInfo] = []
    for fields in _csv_payloads(response, "+QNWINFO:"):
        if len(fields) >= 4:
            networks.append(
                NetworkInfo(
                    technology=fields[0],
                    plmn=fields[1],
                    band=fields[2],
                    channel=_integer(fields[3]),
                )
            )
    return networks


def _parse_serving(response: str) -> list[RadioCell]:
    cells: list[RadioCell] = []
    for fields in _csv_payloads(response, "+QENG:"):
        if not fields or fields[0] == "servingcell":
            continue
        if fields[0] == "LTE" and len(fields) >= 16:
            cells.append(
                RadioCell(
                    technology="LTE",
                    band=_band("LTE", fields[7]),
                    channel=_integer(fields[6]),
                    pci=_integer(fields[5]),
                    mcc=fields[2],
                    mnc=fields[3],
                    cell_id=fields[4],
                    rsrp_dbm=_integer(fields[11]),
                    rsrq_db=_integer(fields[12]),
                    rssi_dbm=_integer(fields[13]),
                    sinr_db=_integer(fields[14]),
                )
            )
        elif fields[0] == "NR5G-NSA" and len(fields) >= 9:
            cells.append(
                RadioCell(
                    technology="NR5G-NSA",
                    band=_band("NR5G", fields[8]),
                    channel=_integer(fields[7]),
                    pci=_integer(fields[3]),
                    mcc=fields[1],
                    mnc=fields[2],
                    rsrp_dbm=_integer(fields[4]),
                    sinr_db=_integer(fields[5]),
                    rsrq_db=_integer(fields[6]),
                )
            )
    return cells


def _parse_neighbors(response: str) -> list[RadioCell]:
    cells: list[RadioCell] = []
    for fields in _csv_payloads(response, "+QENG:"):
        if len(fields) >= 7 and fields[0].startswith("neighbourcell"):
            cells.append(
                RadioCell(
                    technology=fields[1],
                    channel=_integer(fields[2]),
                    pci=_integer(fields[3]),
                    rsrq_db=_integer(fields[4]),
                    rsrp_dbm=_integer(fields[5]),
                    rssi_dbm=_integer(fields[6]),
                )
            )
    return cells


def _parse_qcainfo(response: str) -> list[CarrierComponent]:
    components: list[CarrierComponent] = []
    for fields in _csv_payloads(response, "+QCAINFO:"):
        if len(fields) < 5:
            continue
        band = fields[3]
        technology = "NR5G" if "NR5G" in band else "LTE"
        components.append(
            CarrierComponent(
                role=fields[0],
                technology=technology,
                band=band,
                channel=_integer(fields[1]),
                bandwidth=_integer(fields[2]),
                pci=_integer(fields[5]) if technology == "LTE" and len(fields) > 5 else None,
                rsrp_dbm=_integer(fields[6]) if technology == "LTE" and len(fields) > 6 else None,
                rsrq_db=_integer(fields[7]) if technology == "LTE" and len(fields) > 7 else None,
                rssi_dbm=_integer(fields[8]) if technology == "LTE" and len(fields) > 8 else None,
                sinr_db=_integer(fields[9]) if technology == "LTE" and len(fields) > 9 else None,
            )
        )
    return components


def _parse_cops(response: str) -> list[OperatorInfo]:
    pattern = re.compile(r'\((\d+),"([^"]*)","([^"]*)","(\d+)",(\d+)\)')
    return [
        OperatorInfo(
            status=int(status),
            name=name,
            short_name=short_name,
            plmn=plmn,
            access_technology=int(access_technology),
        )
        for status, name, short_name, plmn, access_technology in pattern.findall(response)
    ]


def _parse_qscan(response: str) -> list[VisibleCell]:
    cells: list[VisibleCell] = []
    for fields in _csv_payloads(response, "+QSCAN:"):
        if len(fields) < 7:
            continue
        channel = _integer(fields[3])
        cells.append(
            VisibleCell(
                technology=fields[0],
                plmn=f"{fields[1]}{fields[2]}",
                channel=channel,
                pci=_integer(fields[4]),
                band=_lte_band(channel) if fields[0] == "LTE" else None,
                rsrp_dbm=_integer(fields[5]),
                rsrq_db=_integer(fields[6]),
            )
        )
    return cells


def _parse_preferences(raw_responses: dict[str, str]) -> list[ModemPreference]:
    queries = (
        'AT+QNWPREFCFG="mode_pref"',
        'AT+QNWPREFCFG="rat_acq_order"',
        'AT+QNWPREFCFG="lte_band"',
        'AT+QNWPREFCFG="nsa_nr5g_band"',
        'AT+QNWPREFCFG="nr5g_band"',
        'AT+QNWPREFCFG="nr5g_disable_mode"',
    )
    preferences: list[ModemPreference] = []
    pattern = re.compile(r'^\+QNWPREFCFG:\s*"([^"]+)",(.+)$', re.MULTILINE)
    for query in queries:
        response = _response(raw_responses, query)
        match = pattern.search(response)
        if match:
            preferences.append(
                ModemPreference(query=query, name=match.group(1), value=match.group(2).strip())
            )
    return preferences


def _csv_payloads(response: str, prefix: str) -> list[list[str]]:
    payloads: list[list[str]] = []
    for line in _content_lines(response, prefix=prefix):
        payload = line.split(":", 1)[1].strip()
        payloads.append(next(csv.reader([payload], skipinitialspace=True)))
    return payloads


def _content_lines(response: str, prefix: str | None) -> list[str]:
    lines = [line.strip() for line in response.splitlines()]
    return [
        line
        for line in lines
        if line and line not in {"OK", "ERROR"} and (prefix is None or line.startswith(prefix))
    ]


def _integer(value: str) -> int | None:
    return int(value) if re.fullmatch(r"-?\d+", value) else None


def _band(technology: str, value: str) -> str | None:
    number = _integer(value)
    return f"{technology} BAND {number}" if number is not None else None


def _lte_band(channel: int | None) -> str | None:
    if channel is None:
        return None
    ranges = (
        (600, 1199, 2),
        (1950, 2399, 4),
        (2400, 2649, 5),
        (5010, 5179, 12),
        (5180, 5279, 13),
        (5280, 5379, 14),
        (9770, 9869, 30),
        (66436, 67335, 66),
    )
    return next(
        (f"LTE BAND {band}" for start, end, band in ranges if start <= channel <= end),
        None,
    )
