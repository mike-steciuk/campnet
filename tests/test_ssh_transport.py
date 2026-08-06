from __future__ import annotations

from campnet.transports.ssh import SSHATTransport


def test_ssh_transport_builds_batch_mode_gl_modem_command() -> None:
    captured: list[tuple[list[str], float]] = []

    def runner(arguments: list[str], timeout_seconds: float) -> str:
        captured.append((arguments, timeout_seconds))
        return "Quectel\nOK\n"

    transport = SSHATTransport("192.168.8.1", runner=runner)

    assert transport.exchange('AT+QENG="servingcell"', 10.0) == "Quectel\nOK\n"
    arguments, timeout = captured[0]
    assert arguments[:5] == [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "PasswordAuthentication=no",
    ]
    assert arguments[-2] == "root@192.168.8.1"
    assert arguments[-1] == "/usr/bin/gl_modem -B 1-1.2 AT 'AT+QENG=\"servingcell\"'"
    assert timeout == 12.0


def test_ssh_transport_rejects_option_injection() -> None:
    try:
        SSHATTransport("-oProxyCommand=bad")
    except ValueError as error:
        assert "unsupported characters" in str(error)
    else:
        raise AssertionError("unsafe SSH target was accepted")


def test_long_command_uses_gl_modem_sat_mode() -> None:
    captured: list[list[str]] = []

    def runner(arguments: list[str], timeout_seconds: float) -> str:
        del timeout_seconds
        captured.append(arguments)
        return "OK\n"

    transport = SSHATTransport("192.168.8.1", runner=runner)
    transport.exchange("AT+QSCAN=1", 240.0)

    assert captured[0][-1] == "/usr/bin/gl_modem -B 1-1.2 SAT sp AT+QSCAN=1"
