"""Hardware-neutral sequential multi-SIM survey orchestration."""

from __future__ import annotations

from campnet.models import JsonValue, ProviderResult, utc_now
from campnet.normalization import normalize_at_result
from campnet.providers.base import CollectionContext, DataProvider
from campnet.radio import (
    merge_shared_and_active_radio,
    radio_snapshot_from_dict,
    radio_snapshot_to_dict,
)
from campnet.sim import SIMSlotController, SIMState


class MultiSIMProvider:
    """Collect shared data once and active-radio data for every discovered slot."""

    def __init__(
        self,
        controller: SIMSlotController,
        shared_provider: DataProvider,
        segment_provider: DataProvider,
    ) -> None:
        self._controller = controller
        self._shared_provider = shared_provider
        self._segment_provider = segment_provider

    @property
    def name(self) -> str:
        # Retain the canonical AT role so existing report parsers read slot one.
        return "at"

    def collect(self, context: CollectionContext) -> ProviderResult:
        inventory = self._controller.inventory()
        original_slot = inventory.active_slot
        raw = dict(inventory.raw_responses)
        errors = list(inventory.errors)
        shared = self._shared_provider.collect(context)
        raw.update(shared.raw_responses)
        errors.extend(shared.errors)

        original_state = self._controller.state(original_slot)
        _merge_evidence(original_state, raw, errors)
        original = self._segment_provider.collect(context)
        raw.update(original.raw_responses)
        errors.extend(original.errors)
        segments: list[JsonValue] = [_segment(original_slot, original_state, original)]
        parent_radio = merge_shared_and_active_radio(
            radio_snapshot_from_dict(shared.data.get("radio")),
            radio_snapshot_from_dict(original.data.get("radio")),
        )
        restored: bool | None = None

        other_slots = tuple(
            slot for slot in inventory.installed_slots if slot != original_slot
        )
        if original_slot in inventory.installed_slots and other_slots:
            try:
                for slot in other_slots:
                    selection = self._controller.select(slot)
                    raw.update(selection.raw_responses)
                    errors.extend(selection.errors)
                    if not selection.selected:
                        segments.append(_segment(slot, SIMState(slot, False, False), None))
                        continue
                    state = self._controller.wait_until_ready(slot)
                    _merge_evidence(state, raw, errors)
                    result = self._segment_provider.collect(context)
                    raw.update(result.raw_responses)
                    errors.extend(result.errors)
                    segments.append(_segment(slot, state, result))
            finally:
                restoration = self._controller.select(original_slot)
                raw.update(restoration.raw_responses)
                errors.extend(restoration.errors)
                restored = restoration.selected
                if restored and original_state.registered:
                    restored_state = self._controller.wait_until_ready(original_slot)
                    _merge_evidence(restored_state, raw, errors)
                    restored = restored_state.ready and restored_state.registered

        return normalize_at_result(
            ProviderResult(
                provider=self.name,
                collected_at=utc_now(),
                data={
                    "commands": original.data.get("commands", []),
                    "radio": radio_snapshot_to_dict(parent_radio),
                    "multi_sim": {
                        "original_slot": original_slot,
                        "installed_slots": list(inventory.installed_slots),
                        "multi_sim_detected": len(inventory.installed_slots) > 1,
                        "dual_sim_detected": len(inventory.installed_slots) == 2,
                        "segments": segments,
                        "restored_original_slot": restored,
                    },
                },
                raw_responses=raw,
                errors=tuple(errors),
            )
        )


def _merge_evidence(state: SIMState, raw: dict[str, str], errors: list[str]) -> None:
    raw.update(state.raw_responses)
    errors.extend(state.errors)


def _segment(
    slot: int | None, state: SIMState, result: ProviderResult | None
) -> JsonValue:
    return {
        "slot": slot,
        "sim_ready": state.ready,
        "registered": state.registered,
        "at_result": result.to_dict() if result is not None else None,
    }
