from __future__ import annotations

from pathlib import Path

from campnet.devices import load_device_profiles


def test_load_device_profile(tmp_path: Path) -> None:
    path = tmp_path / "devices.toml"
    path.write_text(
        """
schema_version = 1
default_device = "router"

[devices.router]
name = "Test Router"
type = "glinet"
ssh_host = "192.168.8.1"
ssh_user = "root"
modem_bus = "1-1.2"

[devices.router.speedtest]
execution = "router"
adapter = "speedtest-cli"
executable = "/usr/bin/speedtest-cli"
expected_interface = "rmnet_mhi0"
timeout_seconds = 180
fallback = "collector"
""".strip(),
        encoding="utf-8",
    )

    device = load_device_profiles(path).select()

    assert device.device_id == "router"
    assert device.modem_bus == "1-1.2"
    assert device.speedtest.execution == "router"
    assert device.speedtest.expected_interface == "rmnet_mhi0"


def test_device_profile_rejects_arbitrary_executable(tmp_path: Path) -> None:
    path = tmp_path / "devices.toml"
    path.write_text(
        """
schema_version = 1
default_device = "router"
[devices.router]
name = "Router"
type = "glinet"
ssh_host = "192.168.8.1"
ssh_user = "root"
modem_bus = "1-1.2"
[devices.router.speedtest]
execution = "router"
adapter = "speedtest-cli"
executable = "speedtest-cli; reboot"
fallback = "none"
""".strip(),
        encoding="utf-8",
    )

    try:
        load_device_profiles(path)
    except ValueError as error:
        assert "absolute path" in str(error)
    else:
        raise AssertionError("unsafe executable was accepted")
