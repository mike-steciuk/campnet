from __future__ import annotations

from unittest.mock import patch

from campnet.cli import (
    _commands_for_profile,
    _confirm_preflight,
    _gnss_policy,
    _preflight_warnings,
    _profile_uses_speedtest,
    build_parser,
)
from campnet.providers import CONTINUOUS_COMMANDS, ONE_OFF_COMMANDS, OPTIMIZE_COMMANDS


def test_collection_profiles_select_expected_commands() -> None:
    assert _commands_for_profile("one-off") == ONE_OFF_COMMANDS
    assert _commands_for_profile("continuous") == CONTINUOUS_COMMANDS
    assert _commands_for_profile("optimize") == OPTIMIZE_COMMANDS


def test_speedtest_is_optimize_only_and_can_be_disabled() -> None:
    assert not _profile_uses_speedtest("one-off", no_speed_test=False)
    assert not _profile_uses_speedtest("continuous", no_speed_test=False)
    assert _profile_uses_speedtest("optimize", no_speed_test=False)
    assert not _profile_uses_speedtest("optimize", no_speed_test=True)


def test_optimize_flag_selects_optimize_profile() -> None:
    args = build_parser().parse_args(("collect", "--optimize"))

    assert args.profile == "optimize"


def test_gnss_profile_policy_preserves_continuous_receiver_state() -> None:
    assert _gnss_policy("one-off", no_gps=False) == (True, 6, True)
    assert _gnss_policy("continuous", no_gps=False) == (False, 1, False)
    assert _gnss_policy("optimize", no_gps=False) is None
    assert _gnss_policy("continuous", no_gps=True) is None


def test_live_one_off_preflight_describes_every_planned_effect() -> None:
    warnings = _preflight_warnings("one-off", no_gps=False, live_hardware=True)

    assert any("operator scan" in warning for warning in warnings)
    assert any("SIM slots" in warning for warning in warnings)
    assert any("GNSS" in warning for warning in warnings)
    assert _preflight_warnings("continuous", no_gps=False, live_hardware=True) == ()
    assert _preflight_warnings("one-off", no_gps=False, live_hardware=False) == ()


def test_yes_flag_is_non_interactive_confirmation() -> None:
    assert _confirm_preflight(("temporarily change state",), assume_yes=True)


def test_preflight_defaults_to_cancellation() -> None:
    with patch("builtins.input", return_value=""):
        assert not _confirm_preflight(("temporarily change state",), assume_yes=False)
