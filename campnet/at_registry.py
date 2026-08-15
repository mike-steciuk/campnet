"""Authoritative metadata registry for AT commands used by CampNet."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class CommandType(StrEnum):
    QUERY = "query"
    TEST = "test/capability query"
    SET = "set/configuration"
    ACTION = "execution/action"
    INTERACTIVE = "interactive"
    URC_CONFIGURATION = "unsolicited result code configuration"


class Safety(StrEnum):
    READ_ONLY = "read-only"
    LOW_RISK = "low-risk configuration"
    CONNECTIVITY_IMPACTING = "connectivity-impacting"
    PERSISTENT = "persistent configuration"
    DESTRUCTIVE = "destructive"
    UNKNOWN = "unknown"


class ValidationStatus(StrEnum):
    DOCUMENTED = "documented"
    UNTESTED = "untested"
    SUPPORTED = "supported"
    SUPPORTED_WITH_QUIRKS = "supported_with_quirks"
    UNSUPPORTED = "unsupported"
    TIMED_OUT = "timed_out"
    INCONCLUSIVE = "inconclusive"
    DANGEROUS_NOT_TESTED = "dangerous_not_tested"


@dataclass(frozen=True, slots=True)
class Parameter:
    name: str
    accepted_values: str
    default: str | None = None
    constraints: str | None = None
    sensitive: bool = False


@dataclass(frozen=True, slots=True)
class ExecutionCharacteristics:
    expected_duration: str
    recommended_timeout_seconds: float
    partial_or_asynchronous: bool = False
    interactive: bool = False
    same_session_required: bool = False


@dataclass(frozen=True, slots=True)
class ATCommand:
    identifier: str
    command: str
    category: str
    summary: str
    purpose: str
    command_type: CommandType
    expected_response: str
    parser: str | None
    safety: Safety
    parameters: tuple[Parameter, ...] = ()
    example_responses: tuple[str, ...] = ()
    side_effects: tuple[str, ...] = ()
    execution: ExecutionCharacteristics = ExecutionCharacteristics("under 10 seconds", 10.0)
    prerequisites: tuple[str, ...] = ()
    related_commands: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def render(self, **values: str) -> str:
        expected = {parameter.name for parameter in self.parameters}
        if set(values) != expected:
            raise ValueError(f"{self.identifier} requires parameters {sorted(expected)}")
        rendered = self.command
        for parameter in self.parameters:
            value = values[parameter.name]
            if not value or any(char in value for char in "\r\n;"):
                raise ValueError(f"unsafe value for {parameter.name}")
            rendered = rendered.replace("<" + parameter.name + ">", value)
        return rendered

    def redact(self, command: str) -> str:
        redacted = command
        for parameter in self.parameters:
            if parameter.sensitive:
                pattern = re.escape(self.command).replace(
                    re.escape("<" + parameter.name + ">"), r"(?P<secret>[^;\r\n]+)"
                )
                match = re.fullmatch(pattern, command)
                if match:
                    redacted = redacted.replace(match.group("secret"), "<redacted>")
        return redacted


@dataclass(frozen=True, slots=True)
class ValidationRecord:
    command_identifier: str
    validated_at: datetime
    modem_manufacturer: str
    modem_model: str
    modem_firmware_revision: str
    router_model: str
    router_firmware_version: str
    operating_system: str
    transport: str
    transport_arguments: tuple[str, ...]
    exact_command: str
    raw_response: str
    normalized_result: dict[str, Any]
    duration_seconds: float
    status: ValidationStatus
    sim_carrier: str | None = None
    radio_access_technology: str | None = None
    registration_state: str | None = None
    tester_notes: str = ""


@dataclass(frozen=True, slots=True)
class NormalizedATError:
    family: str
    raw_text: str
    command_identifier: str
    transport: str
    numeric_code: int | None = None
    interpretation: str = "Unknown modem or transport error"
    confidence: str = "unknown"
    suggested_diagnostics: tuple[str, ...] = field(default_factory=tuple)


def _entry(
    identifier: str,
    command: str,
    category: str,
    summary: str,
    purpose: str,
    *,
    parser: str | None = None,
    timeout: float = 10.0,
    command_type: CommandType = CommandType.QUERY,
    safety: Safety = Safety.READ_ONLY,
    side_effects: tuple[str, ...] = (),
    prerequisites: tuple[str, ...] = (),
    related: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
) -> ATCommand:
    return ATCommand(
        identifier=identifier,
        command=command,
        category=category,
        summary=summary,
        purpose=purpose,
        command_type=command_type,
        expected_response="Command-specific result lines followed by OK, or an exact modem error.",
        parser=parser,
        safety=safety,
        side_effects=side_effects,
        execution=ExecutionCharacteristics(
            "up to several minutes" if timeout > 30 else "normally under 10 seconds", timeout
        ),
        prerequisites=prerequisites,
        related_commands=related,
        references=("Quectel RM520N series AT Commands Manual",),
        notes=notes,
    )


_COMMANDS = (
    _entry(
        "modem.identity",
        "ATI",
        "modem identity",
        "Reports modem identity and revision.",
        "Identifies the modem and firmware associated with a survey.",
        parser="campnet.parsers.quectel.parse_modem",
    ),
    _entry(
        "network.current",
        "AT+QNWINFO",
        "network registration",
        "Reports current access technology, operator, band, and channel.",
        "Records the currently registered network.",
        parser="campnet.parsers.quectel.parse_modem",
    ),
    _entry(
        "network.serving_cell",
        'AT+QENG="servingcell"',
        "serving cell",
        "Reports engineering data for serving cells.",
        "Captures LTE and NR serving-cell radio measurements.",
        parser="campnet.parsers.quectel.parse_modem",
    ),
    _entry(
        "network.neighbor_cells",
        'AT+QENG="neighbourcell"',
        "neighboring cells",
        "Reports neighboring-cell engineering data.",
        "Captures alternatives visible to the modem.",
        parser="campnet.parsers.quectel.parse_modem",
    ),
    _entry(
        "network.carrier_aggregation",
        "AT+QCAINFO",
        "signal quality",
        "Reports active carrier aggregation components.",
        "Records primary and secondary carriers.",
        parser="campnet.parsers.quectel.parse_modem",
    ),
    _entry(
        "config.mode_preference",
        'AT+QNWPREFCFG="mode_pref"',
        "configuration",
        "Queries the radio mode preference.",
        "Snapshots configuration for later restoration.",
        parser="campnet.parsers.quectel.parse_modem",
    ),
    _entry(
        "config.rat_order",
        'AT+QNWPREFCFG="rat_acq_order"',
        "configuration",
        "Queries radio-access acquisition order.",
        "Snapshots configuration for later restoration.",
        parser="campnet.parsers.quectel.parse_modem",
    ),
    _entry(
        "config.lte_bands",
        'AT+QNWPREFCFG="lte_band"',
        "configuration",
        "Queries enabled LTE bands.",
        "Snapshots configuration for later restoration.",
        parser="campnet.parsers.quectel.parse_modem",
    ),
    _entry(
        "config.nsa_bands",
        'AT+QNWPREFCFG="nsa_nr5g_band"',
        "configuration",
        "Queries enabled NSA NR bands.",
        "Snapshots configuration for later restoration.",
        parser="campnet.parsers.quectel.parse_modem",
    ),
    _entry(
        "config.sa_bands",
        'AT+QNWPREFCFG="nr5g_band"',
        "configuration",
        "Queries enabled SA NR bands.",
        "Snapshots configuration for later restoration.",
        parser="campnet.parsers.quectel.parse_modem",
    ),
    _entry(
        "config.nr_mode",
        'AT+QNWPREFCFG="nr5g_disable_mode"',
        "configuration",
        "Queries the NR disable mode.",
        "Snapshots configuration for later restoration.",
        parser="campnet.parsers.quectel.parse_modem",
    ),
    _entry(
        "network.operator_scan",
        "AT+COPS=?",
        "operator scan",
        "Scans operators visible to the modem.",
        "Makes one-off surveys carrier-complete.",
        parser="campnet.parsers.quectel.parse_modem",
        timeout=180.0,
        side_effects=("Long-running scan; may temporarily affect connectivity.",),
    ),
    _entry(
        "network.cell_scan",
        "AT+QSCAN=1",
        "operator scan",
        "Performs a detailed Quectel cell scan.",
        "Captures cells beyond the registered operator.",
        parser="campnet.parsers.quectel.parse_modem",
        timeout=240.0,
        side_effects=("Long-running scan; partial output is firmware-dependent.",),
    ),
    _entry(
        "gnss.state",
        "AT+QGPS?",
        "GPS/GNSS",
        "Queries whether the GNSS engine is enabled.",
        "Prevents CampNet from overwriting pre-existing GNSS state.",
        parser="campnet.providers.gnss._gps_enabled",
    ),
    _entry(
        "gnss.enable",
        "AT+QGPS=1",
        "GPS/GNSS",
        "Starts the GNSS engine.",
        "Temporarily enables GNSS for an authorized one-off fix.",
        command_type=CommandType.SET,
        safety=Safety.LOW_RISK,
        side_effects=("Changes GNSS state and requires restoration when CampNet enabled it.",),
    ),
    _entry(
        "gnss.location",
        "AT+QGPSLOC=2",
        "GPS/GNSS",
        "Queries a GNSS fix in a structured format.",
        "Adds time, position, altitude, and motion to a survey.",
        parser="campnet.providers.gnss._parse_location",
        prerequisites=("GNSS engine enabled and a satellite fix available.",),
        related=("gnss.state", "gnss.enable"),
    ),
    _entry(
        "gnss.stop",
        "AT+QGPSEND",
        "GPS/GNSS",
        "Stops the GNSS engine.",
        "Restores GNSS state after CampNet temporarily enabled it.",
        command_type=CommandType.ACTION,
        safety=Safety.LOW_RISK,
        side_effects=("Changes GNSS state.",),
        related=("gnss.enable",),
    ),
    _entry(
        "sim.active_slot",
        "AT+QUIMSLOT?",
        "SIM",
        "Queries the active SIM slot.",
        "Records the original slot before multi-SIM collection.",
        parser="campnet.providers.multisim.parse_active_slot",
    ),
    _entry(
        "sim.dual_slot_status",
        'AT+QSIMCFG="dual_slot_status"',
        "SIM",
        "Queries dual-slot presence information.",
        "Enables switching only when both cards are explicitly detected.",
        parser="campnet.providers.multisim.parse_installed_slots",
        notes=("Response shape is firmware-dependent; unknown shapes must not trigger switching.",),
    ),
    _entry(
        "sim.readiness",
        "AT+CPIN?",
        "SIM",
        "Queries active SIM readiness.",
        "Waits for the selected card to initialize before collection.",
        parser="campnet.providers.multisim.sim_ready",
    ),
    _entry(
        "network.eps_registration",
        "AT+CEREG?",
        "network registration",
        "Queries EPS registration state.",
        "Waits for home or roaming registration after a slot switch.",
        parser="campnet.providers.multisim.registration_ready",
    ),
)

_SIM_SWITCH = ATCommand(
    identifier="sim.switch_slot",
    command="AT+QUIMSLOT=<slot>",
    category="SIM",
    summary="Selects the active SIM slot.",
    purpose="Collects each installed SIM and restores the original slot.",
    command_type=CommandType.SET,
    expected_response=(
        "OK or an exact modem error; SIM initialization and registration follow asynchronously."
    ),
    parser=None,
    safety=Safety.CONNECTIVITY_IMPACTING,
    parameters=(Parameter("slot", "1 or 2", constraints="single decimal slot number"),),
    side_effects=(
        "Interrupts cellular connectivity.",
        "Persists the selected slot and requires restoration.",
    ),
    execution=ExecutionCharacteristics(
        "switch is immediate; reconnection may take minutes",
        30.0,
        partial_or_asynchronous=True,
    ),
    prerequisites=(
        "Requested slot is populated.",
        "Explicit multi-SIM survey authorization.",
    ),
    related_commands=("sim.active_slot", "sim.readiness", "network.eps_registration"),
    references=("Quectel RG50xQ/RM5xxQ Series AT Commands Manual",),
)

COMMAND_REGISTRY = {item.identifier: item for item in (*_COMMANDS, _SIM_SWITCH)}


def command(identifier: str) -> ATCommand:
    try:
        return COMMAND_REGISTRY[identifier]
    except KeyError as error:
        raise LookupError(f"unknown AT command identifier: {identifier}") from error


def require_authorization(definition: ATCommand, *, authorized: bool) -> None:
    guarded = {Safety.CONNECTIVITY_IMPACTING, Safety.PERSISTENT, Safety.DESTRUCTIVE, Safety.UNKNOWN}
    if definition.safety in guarded and not authorized:
        raise PermissionError(
            f"{definition.identifier} is {definition.safety}; explicit authorization is required"
        )
