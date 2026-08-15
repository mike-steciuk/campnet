"""Provider that captures raw AT responses without transport coupling."""

from __future__ import annotations

from collections.abc import Iterable

from campnet.at import ATClient
from campnet.at_registry import ATCommand, command, require_authorization
from campnet.models import JsonValue, ProviderResult, utc_now
from campnet.providers.base import CollectionContext

CONTINUOUS_COMMANDS = (
    command("modem.identity"),
    command("network.current"),
    command("network.serving_cell"),
    command("network.neighbor_cells"),
    command("network.carrier_aggregation"),
)

CONFIGURATION_COMMANDS = (
    command("config.mode_preference"),
    command("config.rat_order"),
    command("config.lte_bands"),
    command("config.nsa_bands"),
    command("config.sa_bands"),
    command("config.nr_mode"),
)

PASSIVE_SCAN_COMMANDS = (command("network.operator_scan"), command("network.cell_scan"))
SIM_SPECIFIC_COMMANDS = CONTINUOUS_COMMANDS + CONFIGURATION_COMMANDS
ONE_OFF_COMMANDS = SIM_SPECIFIC_COMMANDS + PASSIVE_SCAN_COMMANDS
OPTIMIZE_COMMANDS = SIM_SPECIFIC_COMMANDS


class ATProvider:
    def __init__(
        self,
        client: ATClient,
        commands: Iterable[ATCommand] = CONTINUOUS_COMMANDS,
        *,
        authorized_command_ids: frozenset[str] = frozenset(),
    ) -> None:
        self._client = client
        self._commands = tuple(commands)
        self._authorized_command_ids = authorized_command_ids

    @property
    def name(self) -> str:
        return "at"

    def collect(self, context: CollectionContext) -> ProviderResult:
        del context
        raw_responses: dict[str, str] = {}
        errors: list[str] = []
        commands: list[JsonValue] = []
        for spec in self._commands:
            require_authorization(spec, authorized=spec.identifier in self._authorized_command_ids)
            rendered = spec.render()
            exchange = self._client.execute(
                rendered, timeout_seconds=spec.execution.recommended_timeout_seconds
            )
            attempt_data: list[JsonValue] = []
            for attempt in exchange.attempts:
                key = f"{rendered}#{attempt.attempt}"
                if attempt.response is not None:
                    raw_responses[key] = attempt.response
                if attempt.error is not None:
                    errors.append(f"{key}: {attempt.error}")
                attempt_data.append(
                    {
                        "attempt": attempt.attempt,
                        "response_key": key if attempt.response is not None else None,
                        "error": attempt.error,
                    }
                )
            commands.append(
                {
                    "command_id": spec.identifier,
                    "command": rendered,
                    "succeeded": exchange.succeeded,
                    "attempts": attempt_data,
                }
            )
        return ProviderResult(
            provider=self.name,
            collected_at=utc_now(),
            data={"commands": commands},
            raw_responses=raw_responses,
            errors=tuple(errors),
        )
