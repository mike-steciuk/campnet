from __future__ import annotations

from campnet.at import ATClient
from campnet.at_docs import generate_command_reference
from campnet.at_registry import (
    COMMAND_REGISTRY,
    ATCommand,
    CommandType,
    ExecutionCharacteristics,
    Parameter,
    Safety,
    require_authorization,
)
from campnet.models import SurveyMetadata
from campnet.providers.at import ONE_OFF_COMMANDS, ATProvider
from campnet.providers.base import CollectionContext


def test_registry_identifiers_are_unique_and_metadata_is_complete() -> None:
    assert len(COMMAND_REGISTRY) == 28
    assert len(COMMAND_REGISTRY) == len(set(COMMAND_REGISTRY))
    for identifier, item in COMMAND_REGISTRY.items():
        assert identifier == item.identifier
        assert item.command.startswith("AT")
        assert item.category and item.summary and item.purpose and item.expected_response
        assert item.execution.recommended_timeout_seconds > 0
        assert item.references


def test_every_provider_command_comes_from_registry() -> None:
    assert all(item is COMMAND_REGISTRY[item.identifier] for item in ONE_OFF_COMMANDS)


def test_operator_scan_is_connectivity_impacting() -> None:
    assert COMMAND_REGISTRY["network.operator_scan"].safety is Safety.CONNECTIVITY_IMPACTING


def test_template_rendering_rejects_injection_and_redacts_sensitive_values() -> None:
    item = ATCommand(
        identifier="test.secret",
        command="AT+TEST=<secret>",
        category="diagnostics",
        summary="Test.",
        purpose="Test.",
        command_type=CommandType.SET,
        expected_response="OK",
        parser=None,
        safety=Safety.LOW_RISK,
        parameters=(Parameter("secret", "text", sensitive=True),),
        execution=ExecutionCharacteristics("short", 10),
    )
    assert item.render(secret="abc") == "AT+TEST=abc"
    assert item.redact("AT+TEST=abc") == "AT+TEST=<redacted>"
    try:
        item.render(secret="abc;AT+CFUN=0")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe template value accepted")


def test_guarded_commands_require_explicit_authorization() -> None:
    dangerous = ATCommand(
        identifier="test.erase",
        command="AT+ERASE",
        category="diagnostics",
        summary="Erase.",
        purpose="Test guard.",
        command_type=CommandType.ACTION,
        expected_response="OK",
        parser=None,
        safety=Safety.DESTRUCTIVE,
    )
    try:
        require_authorization(dangerous, authorized=False)
    except PermissionError:
        pass
    else:
        raise AssertionError("dangerous command was not guarded")
    require_authorization(dangerous, authorized=True)


def test_provider_does_not_send_dangerous_command_without_authorization() -> None:
    sent: list[str] = []

    class RecordingTransport:
        def exchange(self, command: str, timeout_seconds: float) -> str:
            del timeout_seconds
            sent.append(command)
            return "OK"

    dangerous = ATCommand(
        identifier="test.erase",
        command="AT+ERASE",
        category="diagnostics",
        summary="Erase.",
        purpose="Test guard.",
        command_type=CommandType.ACTION,
        expected_response="OK",
        parser=None,
        safety=Safety.DESTRUCTIVE,
    )
    provider = ATProvider(ATClient(RecordingTransport()), commands=(dangerous,))
    try:
        provider.collect(CollectionContext(metadata=SurveyMetadata()))
    except PermissionError:
        pass
    else:
        raise AssertionError("dangerous command executed without authorization")
    assert sent == []


def test_session_dependent_batch_is_kept_in_one_exchange() -> None:
    batch = ATCommand(
        identifier="test.batch",
        command="AT+ONE;+TWO?",
        category="diagnostics",
        summary="Run a session-dependent batch.",
        purpose="Verify session grouping.",
        command_type=CommandType.QUERY,
        expected_response="Results followed by OK",
        parser=None,
        safety=Safety.READ_ONLY,
        execution=ExecutionCharacteristics("short", 10, same_session_required=True),
    )
    sent: list[str] = []

    class RecordingTransport:
        def exchange(self, command: str, timeout_seconds: float) -> str:
            del timeout_seconds
            sent.append(command)
            return "OK"

    ATProvider(ATClient(RecordingTransport()), commands=(batch,)).collect(
        CollectionContext(metadata=SurveyMetadata())
    )
    assert sent == ["AT+ONE;+TWO?"]


def test_documentation_contains_every_registered_command() -> None:
    generated = generate_command_reference()
    for item in COMMAND_REGISTRY.values():
        assert f"## `{item.identifier}`" in generated
        assert item.command in generated
    assert generated.count("## `") == len(COMMAND_REGISTRY)
