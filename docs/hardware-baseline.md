# Tested hardware baseline

This document records observations from specific tested environments. These
observations are evidence for compatibility and diagnostics; they are not
universal modem, firmware, carrier, or network assumptions.

## GL.iNet GL-X3000 and Quectel RM520N-GL

- Router: GL.iNet GL-X3000
- Router OS: customized OpenWrt 21.02-SNAPSHOT
- Modem: Quectel RM520N-GL
- Architecture: `aarch64_cortex-a53`
- Modem bus: `1-1.2`
- AT helper: `/usr/bin/gl_modem`
- Normal invocation: `gl_modem -B 1-1.2 AT <command>`
- Long scans: `gl_modem -B 1-1.2 SAT sp <command>`
- Cellular interface observed: `rmnet_mhi0`
- Router speed-test package: `python3-speedtest-cli` 2.1.3
- Router speed-test executable: `/usr/bin/speedtest-cli`

CampNet invokes the collector computer's OpenSSH client and relies on its
key agent and configuration. The tested setup uses a dedicated SSH key for
the router's root account; CampNet does not read or store the router password,
private key, or key passphrase.

## Observed behavior

- AT collection works through `gl_modem` over SSH key authentication.
- One-off scans have observed AT&T, FirstNet, T-Mobile, Verizon, and occasional
  additional PLMNs. Serving-network output alone did not produce a complete
  survey; `AT+COPS=?` and `AT+QSCAN=1` provided broader discovery.
- One tested service state was AT&T LTE band 2 with NSA NR band n5.
- One preference snapshot showed automatic mode, RAT order
  `NR5G:LTE:WCDMA`, broad LTE and NSA bands, SA value `0`, and NR disable mode
  `0`. This describes one environment, not a universal default.
- A focused GNSS run changed `AT+QGPS?` from 0 to 1. `AT+QGPSLOC=2` returned
  `+CME ERROR: 516` before a fix, and `AT+QGPSEND` restored the original
  disabled state. View of sky, antenna, and cold-start duration are plausible
  explanations but remain unproven.
- A router-side Speedtest.net attempt returned HTTP 429. Collector fallback
  worked in an earlier test, while a later field run also reported a speed-test
  failure. Preserve per-run evidence and do not generalize either outcome.
- Provider failures are non-fatal; a failed speed test did not discard modem,
  scan, GNSS, or other successful observations.
- Historical surveys are reparsed with the current code when displayed. A
  stored survey with usable `+QSCAN:` rows can produce a current carrier-signal
  comparison without changing the original JSON or rescanning.
- One Port Sanilac Marina scan from 2026-08-15 recorded `AT+QSCAN=1` but
  received only `OK`, with no `+QSCAN:` rows. It cannot provide historical
  per-carrier signal strength. An `OK` acknowledgement does not prove that the
  scan found cells.
