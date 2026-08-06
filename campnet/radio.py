"""Structured radio-domain observations independent of collection transport."""

from __future__ import annotations

from dataclasses import dataclass


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
