"""Human-readable reports generated from canonical surveys."""

from __future__ import annotations

from collections.abc import Callable

from campnet.models import ProviderResult, Survey
from campnet.parsers import parse_quectel_snapshot
from campnet.radio import RadioCell, RadioSnapshot, VisibleCell

_CARRIERS = {
    "310260": "T-Mobile",
    "310410": "AT&T",
    "311480": "Verizon",
    "313100": "FirstNet",
}


def format_survey(survey: Survey) -> str:
    lines = ["CampNet Cellular Survey", "=" * 23, f"Survey ID:   {survey.survey_id}"]
    lines.extend(_metadata_lines(survey))
    speedtest_result = next(
        (result for result in survey.provider_results if result.provider == "speedtest"), None
    )
    at_result = next(
        (result for result in survey.provider_results if result.provider == "at"), None
    )
    if at_result is not None:
        lines.extend(
            _radio_lines(
                parse_quectel_snapshot(at_result.raw_responses),
                has_speedtest=speedtest_result is not None and speedtest_result.succeeded,
            )
        )
    gnss_result = next(
        (result for result in survey.provider_results if result.provider == "gnss"), None
    )
    if gnss_result is not None:
        lines.extend(_gnss_lines(gnss_result))
    if speedtest_result is not None:
        lines.extend(_speedtest_lines(speedtest_result))
    lines.extend(_provider_lines(survey.provider_results))
    return "\n".join(lines)


def _metadata_lines(survey: Survey) -> list[str]:
    metadata = survey.metadata
    location = metadata.campground or "Unspecified"
    if metadata.site:
        location += f", site {metadata.site}"
    lines = ["", f"Survey time: {survey.timestamp.isoformat()}", f"Location:    {location}"]
    if metadata.device_id:
        lines.append(f"Device:      {metadata.device_id}")
    if metadata.router_placement:
        lines.append(f"Placement:   {metadata.router_placement}")
    if metadata.antenna_configuration:
        lines.append(f"Antenna:     {metadata.antenna_configuration}")
    if metadata.notes:
        lines.append(f"Notes:       {metadata.notes}")
    return lines


def _radio_lines(snapshot: RadioSnapshot, *, has_speedtest: bool) -> list[str]:
    lines: list[str] = []
    if snapshot.modem:
        modem = snapshot.modem
        identity = " ".join(value for value in (modem.manufacturer, modem.model) if value)
        lines.extend(["", "Modem", "-----", identity or "Unknown modem"])
        if modem.revision:
            lines.append(f"Firmware: {modem.revision}")

    lines.extend(["", "Modem preferences", "-----------------"])
    if not snapshot.modem_preferences:
        lines.append("No band or RAT preference snapshot reported.")
    for preference in snapshot.modem_preferences:
        lines.append(f"{preference.name}: {preference.value}")

    lines.extend(["", "Registered networks", "-------------------"])
    if not snapshot.networks:
        lines.append("No registration information reported.")
    for network in snapshot.networks:
        carrier = _CARRIERS.get(network.plmn, f"PLMN {network.plmn}")
        channel = f", channel {network.channel}" if network.channel is not None else ""
        lines.append(f"{carrier}: {network.technology}, {network.band}{channel}")

    lines.extend(_visible_network_lines(snapshot))
    lines.extend(_carrier_signal_lines(snapshot))

    lines.extend(["", "Serving radio", "-------------"])
    if not snapshot.serving_cells:
        lines.append("No serving-cell measurements reported.")
    for cell in snapshot.serving_cells:
        lines.extend(_cell_lines(cell))

    aggregation_heading = _carrier_aggregation_heading(snapshot)
    lines.extend(["", aggregation_heading, "-" * len(aggregation_heading)])
    if not snapshot.carrier_components:
        lines.append("No carrier-aggregation components reported.")
    else:
        lines.append("Active component carriers for the registered connection:")
    for component in snapshot.carrier_components:
        details = [component.role, component.band or component.technology]
        if component.channel is not None:
            details.append(f"channel {component.channel}")
        if component.rsrp_dbm is not None:
            details.append(f"RSRP {component.rsrp_dbm} dBm ({rsrp_quality(component.rsrp_dbm)})")
        lines.append(" | ".join(details))

    lines.extend(["", "Strongest neighboring cells", "---------------------------"])
    neighbors = sorted(
        snapshot.neighbor_cells,
        key=lambda cell: cell.rsrp_dbm if cell.rsrp_dbm is not None else -999,
        reverse=True,
    )
    if not neighbors:
        lines.append("No neighboring-cell measurements reported.")
    for cell in neighbors[:5]:
        signal = _metric("RSRP", cell.rsrp_dbm, "dBm", rsrp_quality)
        lines.append(f"{cell.technology} channel {cell.channel}, PCI {cell.pci}: {signal}")

    lines.extend(["", "Interpretation", "--------------"])
    lines.extend(_interpretation(snapshot, has_speedtest=has_speedtest))
    return lines


def _carrier_aggregation_heading(snapshot: RadioSnapshot) -> str:
    plmns = {network.plmn for network in snapshot.networks if network.plmn}
    plmns.update(
        f"{cell.mcc}{cell.mnc}"
        for cell in snapshot.serving_cells
        if cell.mcc is not None and cell.mnc is not None
    )
    if len(plmns) != 1:
        return "Carrier aggregation (registered carrier unknown)"
    plmn = next(iter(plmns))
    carrier = _CARRIERS.get(plmn, f"PLMN {plmn}")
    return f"Carrier aggregation - {carrier} (PLMN {plmn})"


def _visible_network_lines(snapshot: RadioSnapshot) -> list[str]:
    lines = ["", "Extended carrier scan", "---------------------"]
    if snapshot.operators:
        status_names = {0: "unknown", 1: "available", 2: "current", 3: "forbidden"}
        operator_text = ", ".join(
            f"{operator.name or _CARRIERS.get(operator.plmn, operator.plmn)} "
            f"({status_names.get(operator.status, 'unknown')})"
            for operator in snapshot.operators
        )
        lines.append(f"Operators: {operator_text}")
    if not snapshot.visible_cells:
        lines.append("No visible-cell scan results reported.")
        return lines
    grouped: dict[str, list[VisibleCell]] = {}
    for cell in snapshot.visible_cells:
        grouped.setdefault(cell.plmn, []).append(cell)
    for plmn, cells in grouped.items():
        cells.sort(
            key=lambda cell: cell.rsrp_dbm if cell.rsrp_dbm is not None else -999,
            reverse=True,
        )
        carrier = _CARRIERS.get(plmn, f"PLMN {plmn}")
        best = cells[0]
        signal = _metric("RSRP", best.rsrp_dbm, "dBm", rsrp_quality)
        lines.append(
            f"{carrier}: {len(cells)} cells; best {best.band or best.technology}, {signal}"
        )
    return lines


def _carrier_signal_lines(snapshot: RadioSnapshot) -> list[str]:
    lines = ["", "Signal by carrier", "-----------------"]
    measured = [cell for cell in snapshot.visible_cells if cell.rsrp_dbm is not None]
    if not measured:
        lines.append("No carrier-attributed signal measurements reported.")
        return lines

    operator_names = {
        operator.plmn: operator.name or operator.short_name
        for operator in snapshot.operators
        if operator.name or operator.short_name
    }
    grouped: dict[str, list[VisibleCell]] = {}
    for cell in measured:
        grouped.setdefault(cell.plmn, []).append(cell)

    ranked: list[tuple[str, list[VisibleCell], VisibleCell]] = []
    for plmn, cells in grouped.items():
        cells.sort(key=lambda cell: cell.rsrp_dbm or -999, reverse=True)
        ranked.append((plmn, cells, cells[0]))
    ranked.sort(key=lambda item: item[2].rsrp_dbm or -999, reverse=True)
    strongest_rsrp = ranked[0][2].rsrp_dbm

    lines.append("Ranked by each carrier's strongest passively detected cell:")
    for rank, (plmn, cells, best) in enumerate(ranked, start=1):
        carrier = operator_names.get(plmn) or _CARRIERS.get(plmn, f"PLMN {plmn}")
        rsrp = _metric("RSRP", best.rsrp_dbm, "dBm", rsrp_quality)
        rsrq = _metric("RSRQ", best.rsrq_db, "dB", rsrq_quality)
        radio = best.band or best.technology
        gap = ""
        if strongest_rsrp is not None and best.rsrp_dbm is not None and rank > 1:
            gap = f", {strongest_rsrp - best.rsrp_dbm} dB below strongest"
        cell_word = "cell" if len(cells) == 1 else "cells"
        lines.append(
            f"{rank}. {carrier}: {radio}, {rsrp}, {rsrq}; "
            f"{len(cells)} {cell_word} detected{gap}"
        )
    lines.append(
        "Coverage comparison only: a stronger detected signal may improve reception, "
        "but does not prove registration, capacity, latency, or speed."
    )
    return lines


def _cell_lines(cell: RadioCell) -> list[str]:
    heading = cell.band or cell.technology
    if cell.channel is not None:
        heading += f" (channel {cell.channel})"
    return [
        heading,
        f"  {_metric('RSRP', cell.rsrp_dbm, 'dBm', rsrp_quality)}",
        f"  {_metric('RSRQ', cell.rsrq_db, 'dB', rsrq_quality)}",
        f"  {_metric('SINR', cell.sinr_db, 'dB', sinr_quality)}",
    ]


def _interpretation(snapshot: RadioSnapshot, *, has_speedtest: bool) -> list[str]:
    observations: list[str] = []
    for cell in snapshot.serving_cells:
        label = cell.band or cell.technology
        if cell.rsrp_dbm is not None and cell.rsrp_dbm <= -105:
            observations.append(
                f"- {label} signal strength is weak; placement or antenna changes may help."
            )
        if cell.sinr_db is not None and cell.sinr_db >= 13:
            observations.append(f"- {label} has good signal-to-interference quality.")
    if any(cell.technology == "NR5G-NSA" for cell in snapshot.serving_cells):
        observations.append("- The modem has an active non-standalone 5G secondary connection.")
    if not has_speedtest:
        observations.append("- Throughput and congestion cannot be inferred without a speed test.")
    return observations


def _provider_lines(results: tuple[ProviderResult, ...]) -> list[str]:
    lines = ["", "Collection status", "-----------------"]
    for result in results:
        state = "OK" if result.succeeded else "FAILED"
        lines.append(f"{result.provider}: {state}")
        lines.extend(f"  {error}" for error in result.errors)
    return lines


def _gnss_lines(result: ProviderResult) -> list[str]:
    lines = ["", "GNSS location", "-------------"]
    location = result.data.get("location")
    if not isinstance(location, dict) or not location:
        lines.append("No location fix acquired.")
        return lines
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    lines.append(f"Coordinates: {latitude}, {longitude}")
    altitude = location.get("altitude_m")
    if altitude is not None:
        lines.append(f"Altitude:    {altitude} m")
    hdop = location.get("hdop")
    satellites = location.get("satellites")
    if hdop is not None:
        lines.append(f"HDOP:        {hdop}")
    if satellites is not None:
        lines.append(f"Satellites:  {satellites}")
    return lines


def _speedtest_lines(result: ProviderResult) -> list[str]:
    lines = ["", "Performance", "-----------"]
    if not result.succeeded:
        lines.append("Speed test unavailable or failed.")
        return lines
    _append_measurement(lines, "Download", result.data.get("download_mbps"), "Mbps")
    _append_measurement(lines, "Upload", result.data.get("upload_mbps"), "Mbps")
    _append_measurement(lines, "Latency", result.data.get("latency_ms"), "ms")
    _append_measurement(lines, "Jitter", result.data.get("jitter_ms"), "ms")
    _append_measurement(lines, "Packet loss", result.data.get("packet_loss_percent"), "%")
    isp = result.data.get("isp")
    server = result.data.get("server_name")
    if isinstance(isp, str):
        lines.append(f"ISP:         {isp}")
    if isinstance(server, str):
        lines.append(f"Server:      {server}")
    if result.data.get("execution_scope") == "collector_host":
        lines.append("Measured on: Collector computer")
    elif result.data.get("execution_scope") == "router":
        lines.append("Measured on: Router")
    if result.data.get("fallback_used") is True:
        lines.append("Fallback:    Yes")
        reason = result.data.get("fallback_reason")
        if isinstance(reason, str):
            lines.append(f"Reason:      {reason}")
    return lines


def _append_measurement(lines: list[str], label: str, value: object, unit: str) -> None:
    if isinstance(value, int | float):
        lines.append(f"{label + ':':<12}{value:.3f} {unit}")


def _metric(
    name: str,
    value: int | None,
    unit: str,
    quality: Callable[[int], str],
) -> str:
    if value is None:
        return f"{name}: unavailable"
    return f"{name}: {value} {unit} ({quality(value)})"


def rsrp_quality(value: int) -> str:
    if value >= -80:
        return "Excellent"
    if value >= -90:
        return "Good"
    if value >= -100:
        return "Fair"
    if value >= -110:
        return "Weak"
    return "Very weak"


def rsrq_quality(value: int) -> str:
    if value >= -10:
        return "Excellent"
    if value >= -15:
        return "Good"
    if value >= -20:
        return "Fair"
    return "Poor"


def sinr_quality(value: int) -> str:
    if value >= 20:
        return "Excellent"
    if value >= 13:
        return "Good"
    if value >= 0:
        return "Fair"
    return "Poor"
