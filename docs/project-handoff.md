# CampNet Project Handoff

This is the durable context needed to resume CampNet development on another
computer. Update it when hardware, architecture, known behavior, or priorities
materially change.

## Repository state

- Private repository: `https://github.com/mike-steciuk/campnet`
- Default branch: `main`
- Active branch: `feature/device-speedtest-at-registry`
- Feature commit before this handoff update: `2624f93`
- Python: 3.11 or newer
- Survey schema: 1
- Application version: 0.1.0

The active branch contains device profiles, router/collector speed tests, GNSS
collection, the AT registry, generated reference, and tests. At this writing it
has not been pushed. A local commit reaches the home computer only if the
branch is pushed or the whole repository, including `.git`, is copied.

## Current architecture

```text
Device profile
  -> providers (system, AT, GNSS, speed test)
  -> SurveyCollector
  -> versioned Survey JSON with raw provider responses
  -> Quectel parser and normalized models
  -> human-readable console report
```

The Survey UUID is the stable join key for future related datasets. The Survey
is the canonical boundary for storage, parsing, analysis, and reporting.

AT commands are defined in `campnet/at_registry.py`; runtime command lists use
registry entries rather than duplicate strings. Regenerate the reference with:

```powershell
# Generate the reviewed AT reference from registry metadata.
.\.venv\Scripts\python.exe -m campnet.at_docs
```

## Tested hardware and transport

- Router: GL.iNet GL-X3000
- Router OS: customized OpenWrt 21.02-SNAPSHOT
- Modem: Quectel RM520N-GL
- Architecture: `aarch64_cortex-a53`
- SSH endpoint: `root@192.168.8.1`
- Modem bus: `1-1.2`
- AT helper: `/usr/bin/gl_modem`
- Normal invocation: `gl_modem -B 1-1.2 AT <command>`
- Long scans: `gl_modem -B 1-1.2 SAT sp <command>`
- Cellular interface observed: `rmnet_mhi0`
- Router package: `python3-speedtest-cli` 2.1.3
- Router executable: `/usr/bin/speedtest-cli`

CampNet invokes the computer's OpenSSH client. It never reads or stores the
router password, private key, or key passphrase. Tested access uses a dedicated
key and SSH agent for the router root account.

## Observed behavior

- AT collection works through `gl_modem` over SSH key authentication.
- One-off scans have observed AT&T, FirstNet, T-Mobile, Verizon, and occasional
  additional PLMNs. Serving-network output alone is not a complete survey;
  `AT+COPS=?` and `AT+QSCAN=1` provide broader discovery.
- Tested service was AT&T LTE band 2 with NSA NR band n5.
- One preference snapshot showed automatic mode, RAT order
  `NR5G:LTE:WCDMA`, broad LTE/NSA bands, SA value `0`, and NR disable mode `0`.
  This is one environment's observation, not a universal default.
- GNSS can be enabled. A focused run changed `AT+QGPS?` from 0 to 1, while
  `AT+QGPSLOC=2` returned `+CME ERROR: 516` before a fix. `AT+QGPSEND` then
  restored the original disabled state. View of sky, antenna, and cold-start
  duration are plausible causes but remain unproven.
- Router-side Speedtest.net returned HTTP 429. Collector fallback worked in an
  earlier test, but the latest field run also reported a speed-test failure.
  Preserve its survey error details and diagnose this next.
- Provider failures are non-fatal; a failed speed test does not discard modem,
  scan, GNSS, or other successful observations.

## Private and local files

These are intentionally ignored and must not be committed:

- `devices.toml`: machine-local device configuration
- `surveys/`: raw field surveys and possibly coordinates
- `captures/`, `raw-responses/`, and `tests/fixtures/private/`
- `.venv/`, caches, and `*.private.json`

Survey data can contain IMEI, IMSI, ICCID, cell identifiers, precise GPS
coordinates, public IP addresses, and personal notes. Copy surveys separately
only if history is wanted at home, and keep them out of Git. Only deliberately
sanitized captures belong in tracked fixtures.

`devices.example.toml` is the safe tracked template. The current local profile
is expected to match it unless the router address, interface, or policy changes.

## Home-computer setup

After this branch is pushed, clone and select it:

```powershell
# Clone the private repository and select current development.
git clone https://github.com/mike-steciuk/campnet.git C:\Projects\campnet
Set-Location C:\Projects\campnet
git switch feature/device-speedtest-at-registry
```

Create a fresh environment instead of copying `.venv`:

```powershell
# Install CampNet, verification tools, and collector speed-test support.
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,speedtest]"
```

Create local configuration and configure the SSH key/agent using
`docs/development.md`:

```powershell
# Create an ignored local profile and verify key-only router access.
Copy-Item devices.example.toml devices.toml
ssh -o BatchMode=yes -o PasswordAuthentication=no root@192.168.8.1 true
```

Verify the project:

```powershell
# Run unit tests, lint, and strict static typing.
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check campnet tests
.\.venv\Scripts\python.exe -m mypy campnet tests
```

Run a comprehensive survey from the repository root:

```powershell
# Collect detailed scans, GNSS attempts, configuration, and a speed test.
.\.venv\Scripts\python.exe -m campnet collect `
  --campground "Petoskey State Park" `
  --site "30"
```

Use `--no-speed-test` while diagnosing the current failure, `--no-gps` when a
location attempt is unwanted, or `--profile continuous` for lightweight
collection without slow scans, GNSS state changes, or speed tests.

## Immediate next work

1. Inspect the latest ignored survey's speed-test errors without exposing its
   sensitive contents.
2. Test router and collector clients independently; distinguish HTTP 429 from
   route, DNS, TLS, timeout, and output-format failures. Add a sanitized fixture.
3. Decide whether to use retry/backoff or add a LibreSpeed adapter. Keep it
   configurable per device.
4. Persist structured AT validation records and normalized errors from live
   runs. Schemas exist, but automatic validation-log persistence is incomplete.
5. Improve GNSS diagnostics and optionally configure a longer one-off cold-start
   window while always restoring prior state.
6. Add Markdown/CSV exports and historical comparisons after collection is
   reliable.

## Safety rules

- One-off surveys maximize visibility and may temporarily enable GNSS, then
  restore it. Continuous surveys avoid slow scans and state changes.
- Never execute persistent, destructive, connectivity-impacting, or unknown AT
  commands without explicit authorization and a recovery plan.
- Band tests must snapshot configuration, restore from that snapshot, verify
  every response, re-query restored state, and retain before/after evidence.
- Never place credentials, private keys, passwords, or unredacted surveys in
  source control or chat.
