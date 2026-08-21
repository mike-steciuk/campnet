from __future__ import annotations

from campnet.at import ATClient
from campnet.at_registry import command
from campnet.models import ProviderResult, Survey, SurveyMetadata, utc_now
from campnet.providers.at import ATProvider
from campnet.providers.base import CollectionContext
from campnet.providers.multisim import MultiSIMProvider
from campnet.providers.quectel_sim import (
    QuectelATSimSlotController,
    parse_active_slot,
    parse_installed_slots,
)
from campnet.report import format_survey
from campnet.sim import SIMInventory, SIMSelection, SIMState


class DualSIMTransport:
    def __init__(
        self,
        *,
        both_installed: bool = True,
        alternate_registers: bool = True,
    ) -> None:
        self.active_slot = 1
        self.both_installed = both_installed
        self.alternate_registers = alternate_registers
        self.switches: list[int] = []

    def exchange(self, command_text: str, timeout_seconds: float) -> str:
        del timeout_seconds
        if command_text == "AT+QUIMSLOT?":
            return f"+QUIMSLOT: {self.active_slot}\nOK\n"
        if command_text == 'AT+QSIMCFG="dual_slot_status"':
            status = "1,1" if self.both_installed else "1,0"
            return f'+QSIMCFG: "dual_slot_status",{status}\nOK\n'
        if command_text.startswith("AT+QUIMSLOT="):
            self.active_slot = int(command_text.rsplit("=", 1)[1])
            self.switches.append(self.active_slot)
            return "OK\n"
        if command_text == "AT+CPIN?":
            return "+CPIN: READY\nOK\n"
        if command_text == "AT+CEREG?":
            if self.active_slot == 2 and not self.alternate_registers:
                return "+CEREG: 2,0\nOK\n"
            return "+CEREG: 2,1\nOK\n"
        if command_text == "AT+QNWINFO":
            plmn = "310410" if self.active_slot == 1 else "310260"
            return f'+QNWINFO: "FDD LTE","{plmn}","LTE BAND 2",1125\nOK\n'
        if command_text == "AT+QSCAN=1":
            return '+QSCAN: "LTE",310,410,1125,250,-95,-12,18,111\nOK\n'
        raise AssertionError(f"unexpected command: {command_text}")


def test_multi_sim_collects_both_slots_and_restores_original() -> None:
    transport = DualSIMTransport()
    client = ATClient(transport, retries=0)
    provider = MultiSIMProvider(
        QuectelATSimSlotController(
            client, registration_attempts=1, sleeper=lambda seconds: None, authorized=True
        ),
        ATProvider(client, commands=(command("network.cell_scan"),)),
        ATProvider(client, commands=(command("network.current"),)),
    )

    result = provider.collect(CollectionContext(metadata=SurveyMetadata()))

    state = result.data["multi_sim"]
    assert isinstance(state, dict)
    assert state["dual_sim_detected"] is True
    assert state["original_slot"] == 1
    assert state["restored_original_slot"] is True
    assert transport.switches == [2, 1]
    assert transport.active_slot == 1
    segments = state["segments"]
    assert isinstance(segments, list)
    assert [segment["slot"] for segment in segments if isinstance(segment, dict)] == [1, 2]

    survey = Survey(
        timestamp=utc_now(),
        metadata=SurveyMetadata(),
        provider_results=(result,),
    )
    report = format_survey(survey)
    assert "Multi-SIM collection" in report
    assert "Original restored:   yes" in report
    assert "SIM slot 1 | registered | AT&T (310410)" in report
    assert "SIM slot 2 | registered | T-Mobile (310260)" in report
    assert "Signal by carrier" in report
    assert "1. AT&T: LTE BAND 2" in report


def test_single_detected_sim_never_switches() -> None:
    transport = DualSIMTransport(both_installed=False)
    client = ATClient(transport, retries=0)
    provider = MultiSIMProvider(
        QuectelATSimSlotController(client, authorized=True),
        ATProvider(client, commands=(command("network.cell_scan"),)),
        ATProvider(client, commands=(command("network.current"),)),
    )

    result = provider.collect(CollectionContext(metadata=SurveyMetadata()))

    state = result.data["multi_sim"]
    assert isinstance(state, dict)
    assert state["dual_sim_detected"] is False
    assert transport.switches == []


def test_alternate_registration_failure_still_restores_original() -> None:
    transport = DualSIMTransport(alternate_registers=False)
    client = ATClient(transport, retries=0)
    provider = MultiSIMProvider(
        QuectelATSimSlotController(
            client, registration_attempts=1, sleeper=lambda seconds: None, authorized=True
        ),
        ATProvider(client, commands=(command("network.cell_scan"),)),
        ATProvider(client, commands=(command("network.current"),)),
    )

    result = provider.collect(CollectionContext(metadata=SurveyMetadata()))

    state = result.data["multi_sim"]
    assert isinstance(state, dict)
    assert state["restored_original_slot"] is True
    assert transport.switches == [2, 1]
    assert transport.active_slot == 1
    assert any("slot 2 did not register" in error for error in result.errors)


def test_sim_inventory_parsers_are_conservative() -> None:
    assert parse_active_slot("+QUIMSLOT: 2\nOK") == 2
    assert parse_installed_slots('+QSIMCFG: "dual_slot_status",1,1\nOK') == (1, 2)
    assert parse_installed_slots("OK") == ()


def test_sim_switch_requires_external_authorization() -> None:
    transport = DualSIMTransport()
    controller = QuectelATSimSlotController(ATClient(transport, retries=0))

    try:
        controller.select(2)
    except PermissionError:
        pass
    else:
        raise AssertionError("SIM switch executed without preflight authorization")
    assert transport.switches == []


class ThreeSlotController:
    def __init__(self) -> None:
        self.active = 2
        self.selections: list[int] = []

    def inventory(self) -> SIMInventory:
        return SIMInventory(active_slot=2, installed_slots=(1, 2, 3))

    def state(self, slot: int | None) -> SIMState:
        return SIMState(slot, ready=True, registered=True)

    def select(self, slot: int) -> SIMSelection:
        self.active = slot
        self.selections.append(slot)
        return SIMSelection(slot, selected=True)

    def wait_until_ready(self, slot: int) -> SIMState:
        return SIMState(slot, ready=True, registered=True)


class SlotRecordingProvider:
    name = "at"

    def __init__(self, controller: ThreeSlotController) -> None:
        self.controller = controller

    def collect(self, context: CollectionContext) -> ProviderResult:
        del context
        return ProviderResult(
            provider=self.name,
            collected_at=utc_now(),
            data={"commands": [], "observed_slot": self.controller.active},
        )


def test_generic_orchestrator_visits_every_discovered_slot_then_restores() -> None:
    controller = ThreeSlotController()
    provider = SlotRecordingProvider(controller)
    result = MultiSIMProvider(controller, provider, provider).collect(
        CollectionContext(metadata=SurveyMetadata())
    )

    state = result.data["multi_sim"]
    assert isinstance(state, dict)
    assert state["installed_slots"] == [1, 2, 3]
    assert state["multi_sim_detected"] is True
    assert state["dual_sim_detected"] is False
    segments = state["segments"]
    assert isinstance(segments, list)
    assert [segment["slot"] for segment in segments if isinstance(segment, dict)] == [2, 1, 3]
    assert controller.selections == [1, 3, 2]
    assert controller.active == 2
