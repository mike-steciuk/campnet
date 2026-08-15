"""Hardware-neutral SIM-slot control contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SIMInventory:
    """Slots reported by a device and the slot active when queried."""

    active_slot: int | None
    installed_slots: tuple[int, ...]
    raw_responses: dict[str, str] = field(default_factory=dict)
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SIMState:
    """Readiness and network-registration state for the selected slot."""

    slot: int | None
    ready: bool
    registered: bool
    raw_responses: dict[str, str] = field(default_factory=dict)
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SIMSelection:
    """Result and evidence from selecting and verifying a slot."""

    slot: int
    selected: bool
    raw_responses: dict[str, str] = field(default_factory=dict)
    errors: tuple[str, ...] = ()


class SIMSlotController(Protocol):
    """Device adapter used by generic multi-SIM survey orchestration."""

    def inventory(self) -> SIMInventory: ...

    def state(self, slot: int | None) -> SIMState: ...

    def select(self, slot: int) -> SIMSelection: ...

    def wait_until_ready(self, slot: int) -> SIMState: ...
