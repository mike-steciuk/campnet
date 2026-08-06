"""Live AT transport through OpenSSH and GL.iNet's modem helper."""

from __future__ import annotations

import re
import shlex
import subprocess
from collections.abc import Callable

CommandRunner = Callable[[list[str], float], str]
_SAFE_TARGET = re.compile(r"^[A-Za-z0-9_.:@-]+$")
_SAFE_BUS = re.compile(r"^[A-Za-z0-9_.:-]+$")


class SSHATTransport:
    """Send AT commands without reading or storing SSH credentials."""

    def __init__(
        self,
        host: str,
        *,
        user: str = "root",
        modem_bus: str = "1-1.2",
        ssh_executable: str = "ssh",
        runner: CommandRunner | None = None,
    ) -> None:
        target = f"{user}@{host}"
        if not _SAFE_TARGET.fullmatch(target) or target.startswith("-"):
            raise ValueError("SSH user and host contain unsupported characters")
        if not _SAFE_BUS.fullmatch(modem_bus) or modem_bus.startswith("-"):
            raise ValueError("modem bus contains unsupported characters")
        self._target = target
        self._modem_bus = modem_bus
        self._ssh_executable = ssh_executable
        self._runner = runner or _run_command

    def exchange(self, command: str, timeout_seconds: float) -> str:
        connect_timeout = max(1, min(round(timeout_seconds), 30))
        modem_arguments = ["/usr/bin/gl_modem", "-B", self._modem_bus]
        if timeout_seconds > 30:
            modem_arguments.extend(("SAT", "sp", command))
        else:
            modem_arguments.extend(("AT", command))
        remote_command = " ".join(shlex.quote(part) for part in modem_arguments)
        arguments = [
            self._ssh_executable,
            "-o",
            "BatchMode=yes",
            "-o",
            "PasswordAuthentication=no",
            "-o",
            f"ConnectTimeout={connect_timeout}",
            self._target,
            remote_command,
        ]
        return self._runner(arguments, timeout_seconds + 2)


def _run_command(arguments: list[str], timeout_seconds: float) -> str:
    try:
        completed = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise TimeoutError("SSH AT command timed out") from error
    except FileNotFoundError as error:
        raise RuntimeError("OpenSSH client was not found on PATH") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown SSH error"
        raise ConnectionError(detail)
    return completed.stdout
