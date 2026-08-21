"""Structured radio-domain observations independent of collection transport."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import cast

from campnet.models import JsonValue


@dataclass(frozen=True, slots=True)
class ModemInfo:
    manufacturer: str | None = None
    model: str | None = None
    revision: str | None = None


@dataclass(frozen=True, slots=True)
class NetworkInfo:
    technology: str
    plmn: str
    band: str
    channel: int | None


@dataclass(frozen=True, slots=True)
class RadioCell:
    technology: str
    band: str | None = None
    channel: int | None = None
    pci: int | None = None
    mcc: str | None = None
    mnc: str | None = None
    cell_id: str | None = None
    rsrp_dbm: int | None = None
    rsrq_db: int | None = None
    rssi_dbm: int | None = None
    sinr_db: int | None = None


@dataclass(frozen=True, slots=True)
class CarrierComponent:
    role: str
    technology: str
    band: str | None
    channel: int | None
    bandwidth: int | None
    pci: int | None = None
    rsrp_dbm: int | None = None
    rsrq_db: int | None = None
    rssi_dbm: int | None = None
    sinr_db: int | None = None


@dataclass(frozen=True, slots=True)
class OperatorInfo:
    status: int
    name: str
    short_name: str
    plmn: str
    access_technology: int


@dataclass(frozen=True, slots=True)
class VisibleCell:
    technology: str
    plmn: str
    channel: int | None
    pci: int | None
    band: str | None
    rsrp_dbm: int | None
    rsrq_db: int | None


@dataclass(frozen=True, slots=True)
class ModemPreference:
    query: str
    name: str
    value: str


@dataclass(frozen=True, slots=True)
class RadioSnapshot:
    modem: ModemInfo | None = None
    networks: tuple[NetworkInfo, ...] = ()
    serving_cells: tuple[RadioCell, ...] = ()
    neighbor_cells: tuple[RadioCell, ...] = ()
    carrier_components: tuple[CarrierComponent, ...] = ()
    operators: tuple[OperatorInfo, ...] = ()
    visible_cells: tuple[VisibleCell, ...] = ()
    modem_preferences: tuple[ModemPreference, ...] = ()


def merge_shared_and_active_radio(
    shared: RadioSnapshot, active: RadioSnapshot
) -> RadioSnapshot:
    """Combine passive environment observations with active-connection data."""

    return RadioSnapshot(
        modem=active.modem or shared.modem,
        networks=active.networks or shared.networks,
        serving_cells=active.serving_cells or shared.serving_cells,
        neighbor_cells=active.neighbor_cells or shared.neighbor_cells,
        carrier_components=active.carrier_components or shared.carrier_components,
        operators=shared.operators or active.operators,
        visible_cells=shared.visible_cells or active.visible_cells,
        modem_preferences=active.modem_preferences or shared.modem_preferences,
    )


def radio_snapshot_to_dict(snapshot: RadioSnapshot) -> dict[str, JsonValue]:
    document: object = json.loads(json.dumps(asdict(snapshot)))
    if not isinstance(document, dict):
        raise TypeError("radio snapshot did not serialize to an object")
    return cast(dict[str, JsonValue], document)


def radio_snapshot_from_dict(value: object) -> RadioSnapshot:
    if not isinstance(value, dict):
        return RadioSnapshot()
    modem_value = value.get("modem")
    modem = (
        ModemInfo(
            manufacturer=_optional_string(modem_value.get("manufacturer")),
            model=_optional_string(modem_value.get("model")),
            revision=_optional_string(modem_value.get("revision")),
        )
        if isinstance(modem_value, dict)
        else None
    )
    return RadioSnapshot(
        modem=modem,
        networks=tuple(
            NetworkInfo(
                technology=_string(item.get("technology")),
                plmn=_string(item.get("plmn")),
                band=_string(item.get("band")),
                channel=_optional_int(item.get("channel")),
            )
            for item in _records(value.get("networks"))
        ),
        serving_cells=tuple(_radio_cell(item) for item in _records(value.get("serving_cells"))),
        neighbor_cells=tuple(_radio_cell(item) for item in _records(value.get("neighbor_cells"))),
        carrier_components=tuple(
            CarrierComponent(
                role=_string(item.get("role")),
                technology=_string(item.get("technology")),
                band=_optional_string(item.get("band")),
                channel=_optional_int(item.get("channel")),
                bandwidth=_optional_int(item.get("bandwidth")),
                pci=_optional_int(item.get("pci")),
                rsrp_dbm=_optional_int(item.get("rsrp_dbm")),
                rsrq_db=_optional_int(item.get("rsrq_db")),
                rssi_dbm=_optional_int(item.get("rssi_dbm")),
                sinr_db=_optional_int(item.get("sinr_db")),
            )
            for item in _records(value.get("carrier_components"))
        ),
        operators=tuple(
            OperatorInfo(
                status=_int(item.get("status")),
                name=_string(item.get("name")),
                short_name=_string(item.get("short_name")),
                plmn=_string(item.get("plmn")),
                access_technology=_int(item.get("access_technology")),
            )
            for item in _records(value.get("operators"))
        ),
        visible_cells=tuple(
            VisibleCell(
                technology=_string(item.get("technology")),
                plmn=_string(item.get("plmn")),
                channel=_optional_int(item.get("channel")),
                pci=_optional_int(item.get("pci")),
                band=_optional_string(item.get("band")),
                rsrp_dbm=_optional_int(item.get("rsrp_dbm")),
                rsrq_db=_optional_int(item.get("rsrq_db")),
            )
            for item in _records(value.get("visible_cells"))
        ),
        modem_preferences=tuple(
            ModemPreference(
                query=_string(item.get("query")),
                name=_string(item.get("name")),
                value=_string(item.get("value")),
            )
            for item in _records(value.get("modem_preferences"))
        ),
    )


def _radio_cell(item: dict[object, object]) -> RadioCell:
    return RadioCell(
        technology=_string(item.get("technology")),
        band=_optional_string(item.get("band")),
        channel=_optional_int(item.get("channel")),
        pci=_optional_int(item.get("pci")),
        mcc=_optional_string(item.get("mcc")),
        mnc=_optional_string(item.get("mnc")),
        cell_id=_optional_string(item.get("cell_id")),
        rsrp_dbm=_optional_int(item.get("rsrp_dbm")),
        rsrq_db=_optional_int(item.get("rsrq_db")),
        rssi_dbm=_optional_int(item.get("rssi_dbm")),
        sinr_db=_optional_int(item.get("sinr_db")),
    )


def _records(value: object) -> tuple[dict[object, object], ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def _string(value: object) -> str:
    return value if isinstance(value, str) else ""


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _int(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None
