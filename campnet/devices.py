"""Validated, versioned device profiles for repeatable collection."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.-]+$")
_SAFE_HOST = re.compile(r"^[A-Za-z0-9_.:-]+$")


@dataclass(frozen=True, slots=True)
class DeviceSpeedTestConfig:
    execution: str
    adapter: str
    executable: str
    expected_interface: str | None
    timeout_seconds: float
    fallback: str


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    device_id: str
    name: str
    device_type: str
    ssh_host: str
    ssh_user: str
    modem_bus: str
    speedtest: DeviceSpeedTestConfig


@dataclass(frozen=True, slots=True)
class DeviceProfiles:
    default_device: str
    devices: dict[str, DeviceProfile]

    def select(self, device_id: str | None = None) -> DeviceProfile:
        selected = device_id or self.default_device
        try:
            return self.devices[selected]
        except KeyError as error:
            raise ValueError(f"unknown device profile: {selected}") from error


def load_device_profiles(path: Path) -> DeviceProfiles:
    document = tomllib.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1:
        raise ValueError("unsupported device configuration schema")
    default_device = document.get("default_device")
    device_documents = document.get("devices")
    if not isinstance(default_device, str) or not isinstance(device_documents, dict):
        raise ValueError("device configuration requires default_device and devices")
    devices: dict[str, DeviceProfile] = {}
    for device_id, untyped in device_documents.items():
        if not isinstance(device_id, str) or not isinstance(untyped, dict):
            raise ValueError("invalid device profile")
        devices[device_id] = _parse_device(device_id, cast(dict[str, object], untyped))
    profiles = DeviceProfiles(default_device=default_device, devices=devices)
    profiles.select()
    return profiles


def _parse_device(device_id: str, value: dict[str, object]) -> DeviceProfile:
    _validate_identifier("device ID", device_id)
    name = _required_string(value, "name")
    device_type = _required_string(value, "type")
    if device_type != "glinet":
        raise ValueError(f"unsupported device type: {device_type}")
    ssh_host = _required_string(value, "ssh_host")
    ssh_user = _required_string(value, "ssh_user")
    modem_bus = _required_string(value, "modem_bus")
    if not _SAFE_HOST.fullmatch(ssh_host):
        raise ValueError("SSH host contains unsupported characters")
    _validate_identifier("SSH user", ssh_user)
    _validate_identifier("modem bus", modem_bus)
    speedtest_value = value.get("speedtest")
    if not isinstance(speedtest_value, dict):
        raise ValueError(f"device {device_id} requires speedtest configuration")
    speedtest = _parse_speedtest(cast(dict[str, object], speedtest_value))
    return DeviceProfile(
        device_id=device_id,
        name=name,
        device_type=device_type,
        ssh_host=ssh_host,
        ssh_user=ssh_user,
        modem_bus=modem_bus,
        speedtest=speedtest,
    )


def _parse_speedtest(value: dict[str, object]) -> DeviceSpeedTestConfig:
    execution = _required_string(value, "execution")
    adapter = _required_string(value, "adapter")
    executable = _required_string(value, "executable")
    fallback = _required_string(value, "fallback")
    expected_interface = value.get("expected_interface")
    timeout = value.get("timeout_seconds", 180)
    if execution not in {"router", "collector"}:
        raise ValueError("speedtest execution must be router or collector")
    if adapter != "speedtest-cli":
        raise ValueError(f"unsupported speedtest adapter: {adapter}")
    if not PurePosixPath(executable).is_absolute():
        raise ValueError("router speedtest executable must be an absolute path")
    if expected_interface is not None:
        if not isinstance(expected_interface, str):
            raise ValueError("expected_interface must be a string")
        _validate_identifier("expected interface", expected_interface)
    if not isinstance(timeout, int | float) or not 10 <= float(timeout) <= 600:
        raise ValueError("speedtest timeout must be between 10 and 600 seconds")
    if fallback not in {"collector", "none"}:
        raise ValueError("speedtest fallback must be collector or none")
    return DeviceSpeedTestConfig(
        execution=execution,
        adapter=adapter,
        executable=executable,
        expected_interface=expected_interface,
        timeout_seconds=float(timeout),
        fallback=fallback,
    )


def _required_string(value: dict[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a non-empty string")
    return item


def _validate_identifier(label: str, value: str) -> None:
    if not _SAFE_IDENTIFIER.fullmatch(value) or value.startswith("-"):
        raise ValueError(f"{label} contains unsupported characters")
