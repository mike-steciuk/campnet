"""Provider that captures raw AT responses without transport coupling."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from campnet.at import ATClient
from campnet.models import JsonValue, ProviderResult, utc_now
from campnet.providers.base import CollectionContext


@dataclass(frozen=True, slots=True)
class ATCommandSpec:
    command: str
    timeout_seconds: float = 10.0


CONTINUOUS_COMMANDS = (
    ATCommandSpec("ATI"),
    ATCommandSpec("AT+QNWINFO"),
    ATCommandSpec('AT+QENG="servingcell"'),
    ATCommandSpec('AT+QENG="neighbourcell"'),
    ATCommandSpec("AT+QCAINFO"),
)

ONE_OFF_COMMANDS = CONTINUOUS_COMMANDS + (
    ATCommandSpec('AT+QNWPREFCFG="mode_pref"'),
    ATCommandSpec('AT+QNWPREFCFG="rat_acq_order"'),
    ATCommandSpec('AT+QNWPREFCFG="lte_band"'),
    ATCommandSpec('AT+QNWPREFCFG="nsa_nr5g_band"'),
    ATCommandSpec('AT+QNWPREFCFG="nr5g_band"'),
    ATCommandSpec('AT+QNWPREFCFG="nr5g_disable_mode"'),
    ATCommandSpec("AT+COPS=?", timeout_seconds=180.0),
    ATCommandSpec("AT+QSCAN=1", timeout_seconds=240.0),
)


class ATProvider:
    def __init__(
        self,
        client: ATClient,
        commands: Iterable[ATCommandSpec] = CONTINUOUS_COMMANDS,
    ) -> None:
        self._client = client
        self._commands = tuple(commands)

    @property
    def name(self) -> str:
        return "at"

    def collect(self, context: CollectionContext) -> ProviderResult:
        del context
        raw_responses: dict[str, str] = {}
        errors: list[str] = []
        commands: list[JsonValue] = []
        for spec in self._commands:
            command = spec.command
            exchange = self._client.execute(command, timeout_seconds=spec.timeout_seconds)
            attempt_data: list[JsonValue] = []
            for attempt in exchange.attempts:
                key = f"{command}#{attempt.attempt}"
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
                {"command": command, "succeeded": exchange.succeeded, "attempts": attempt_data}
            )
        return ProviderResult(
            provider=self.name,
            collected_at=utc_now(),
            data={"commands": commands},
            raw_responses=raw_responses,
            errors=tuple(errors),
        )
