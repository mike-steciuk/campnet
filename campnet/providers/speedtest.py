"""Auto-detected speed-test providers with normalized and raw results."""

from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from campnet.models import JsonValue, ProviderResult, utc_now
from campnet.providers.base import CollectionContext


class SpeedTestAdapter(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def execution_scope(self) -> str: ...

    def run(self, timeout_seconds: float) -> tuple[dict[str, JsonValue], str]: ...


@dataclass(frozen=True, slots=True)
class CommandSpeedTestAdapter:
    executable: Path
    official_ookla: bool

    @property
    def name(self) -> str:
        return "ookla" if self.official_ookla else "speedtest-cli"

    @property
    def execution_scope(self) -> str:
        return "collector_host"

    def run(self, timeout_seconds: float) -> tuple[dict[str, JsonValue], str]:
        arguments = (
            [
                str(self.executable),
                "--accept-license",
                "--accept-gdpr",
                "--format=json",
            ]
            if self.official_ookla
            else [str(self.executable), "--json", "--secure"]
        )
        try:
            completed = subprocess.run(
                arguments,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise TimeoutError("speed test timed out") from error
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
            raise RuntimeError(f"speed test failed: {detail}")
        raw = completed.stdout.strip()
        value: object = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("speed-test result must be a JSON object")
        document = cast(dict[str, JsonValue], value)
        normalized = (
            _normalize_ookla(document)
            if self.official_ookla
            else _normalize_speedtest_cli(document)
        )
        return normalized, raw


@dataclass(frozen=True, slots=True)
class SSHSpeedTestAdapter:
    host: str
    user: str = "root"
    executable: str = "/usr/bin/speedtest-cli"
    expected_interface: str | None = None
    ssh_executable: str = "ssh"

    @property
    def name(self) -> str:
        return "speedtest-cli"

    @property
    def execution_scope(self) -> str:
        return "router"

    def run(self, timeout_seconds: float) -> tuple[dict[str, JsonValue], str]:
        target = f"{self.user}@{self.host}"
        if not re.fullmatch(r"[A-Za-z0-9_.:@-]+", target) or target.startswith("-"):
            raise ValueError("unsafe SSH speed-test target")
        if not self.executable.startswith("/") or not re.fullmatch(
            r"/[A-Za-z0-9_./-]+", self.executable
        ):
            raise ValueError("unsafe router speed-test executable")
        if self.expected_interface is not None:
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", self.expected_interface):
                raise ValueError("unsafe expected interface")
            route = _run_ssh(
                self.ssh_executable,
                target,
                "ip -4 route get 1.1.1.1",
                min(timeout_seconds, 15),
            )
            match = re.search(r"\bdev\s+(\S+)", route)
            actual_interface = match.group(1) if match else None
            if actual_interface != self.expected_interface:
                raise RuntimeError(
                    f"router default route uses {actual_interface or 'an unknown interface'}, "
                    f"expected {self.expected_interface}"
                )
        command = " ".join(shlex.quote(part) for part in (self.executable, "--json", "--secure"))
        raw = _run_ssh(self.ssh_executable, target, command, timeout_seconds).strip()
        value: object = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("router speed-test result must be a JSON object")
        return _normalize_speedtest_cli(cast(dict[str, JsonValue], value)), raw


class SpeedTestProvider:
    def __init__(
        self,
        adapter: SpeedTestAdapter | None = None,
        *,
        fallback_adapter: SpeedTestAdapter | None = None,
        timeout_seconds: float = 180.0,
    ):
        self._adapter = adapter
        self._fallback_adapter = fallback_adapter
        self._timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "speedtest"

    def collect(self, context: CollectionContext) -> ProviderResult:
        del context
        adapter = self._adapter or discover_speedtest_adapter()
        if adapter is None:
            return ProviderResult(
                provider=self.name,
                collected_at=utc_now(),
                errors=("No supported speed-test client found",),
            )
        adapters = [adapter]
        if self._fallback_adapter is not None:
            adapters.append(self._fallback_adapter)
        failures: list[str] = []
        for index, candidate in enumerate(adapters):
            try:
                data, raw = candidate.run(self._timeout_seconds)
                return ProviderResult(
                    provider=self.name,
                    collected_at=utc_now(),
                    data={
                        "tool": candidate.name,
                        "execution_scope": candidate.execution_scope,
                        "fallback_used": index > 0,
                        "fallback_reason": "; ".join(failures) if failures else None,
                        **data,
                    },
                    raw_responses={"result.json": raw},
                )
            except Exception as error:
                failures.append(f"{candidate.execution_scope}: {type(error).__name__}: {error}")
        return ProviderResult(
            provider=self.name,
            collected_at=utc_now(),
            data={"tool": adapter.name},
            errors=tuple(failures),
        )


def discover_speedtest_adapter() -> CommandSpeedTestAdapter | None:
    speedtest = _find_executable("speedtest")
    if speedtest:
        official = _is_official_ookla(Path(speedtest))
        if official:
            return CommandSpeedTestAdapter(Path(speedtest), official_ookla=True)
    legacy = _find_executable("speedtest-cli")
    if legacy:
        return CommandSpeedTestAdapter(Path(legacy), official_ookla=False)
    if speedtest:
        return CommandSpeedTestAdapter(Path(speedtest), official_ookla=False)
    return None


def _find_executable(name: str) -> str | None:
    discovered = shutil.which(name)
    if discovered:
        return discovered
    scripts_directory = Path(sys.executable).parent
    candidates = (scripts_directory / name, scripts_directory / f"{name}.exe")
    return next((str(candidate) for candidate in candidates if candidate.is_file()), None)


def _is_official_ookla(executable: Path) -> bool:
    try:
        completed = subprocess.run(
            [str(executable), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return "ookla" in (completed.stdout + completed.stderr).lower()


def _run_ssh(executable: str, target: str, remote_command: str, timeout_seconds: float) -> str:
    arguments = [
        executable,
        "-o",
        "BatchMode=yes",
        "-o",
        "PasswordAuthentication=no",
        "-o",
        "ConnectTimeout=10",
        target,
        remote_command,
    ]
    try:
        completed = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise TimeoutError("router speed test timed out") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown SSH error"
        raise RuntimeError(detail)
    return completed.stdout


def _normalize_ookla(value: dict[str, JsonValue]) -> dict[str, JsonValue]:
    ping = _dict(value.get("ping"))
    download = _dict(value.get("download"))
    upload = _dict(value.get("upload"))
    server = _dict(value.get("server"))
    result = _dict(value.get("result"))
    return {
        "download_mbps": _bandwidth_mbps(download.get("bandwidth")),
        "upload_mbps": _bandwidth_mbps(upload.get("bandwidth")),
        "latency_ms": _number(ping.get("latency")),
        "jitter_ms": _number(ping.get("jitter")),
        "packet_loss_percent": _number(value.get("packetLoss")),
        "isp": value.get("isp") if isinstance(value.get("isp"), str) else None,
        "server_name": server.get("name") if isinstance(server.get("name"), str) else None,
        "server_location": server.get("location")
        if isinstance(server.get("location"), str)
        else None,
        "result_url": result.get("url") if isinstance(result.get("url"), str) else None,
    }


def _normalize_speedtest_cli(value: dict[str, JsonValue]) -> dict[str, JsonValue]:
    server = _dict(value.get("server"))
    client = _dict(value.get("client"))
    return {
        "download_mbps": _bits_mbps(value.get("download")),
        "upload_mbps": _bits_mbps(value.get("upload")),
        "latency_ms": _number(value.get("ping")),
        "jitter_ms": None,
        "packet_loss_percent": None,
        "isp": client.get("isp") if isinstance(client.get("isp"), str) else None,
        "server_name": server.get("sponsor") if isinstance(server.get("sponsor"), str) else None,
        "server_location": server.get("name") if isinstance(server.get("name"), str) else None,
        "result_url": value.get("share") if isinstance(value.get("share"), str) else None,
    }


def _dict(value: JsonValue | None) -> dict[str, JsonValue]:
    return value if isinstance(value, dict) else {}


def _number(value: JsonValue | None) -> float | None:
    return float(value) if isinstance(value, int | float) else None


def _bandwidth_mbps(value: JsonValue | None) -> float | None:
    number = _number(value)
    return round(number * 8 / 1_000_000, 3) if number is not None else None


def _bits_mbps(value: JsonValue | None) -> float | None:
    number = _number(value)
    return round(number / 1_000_000, 3) if number is not None else None
