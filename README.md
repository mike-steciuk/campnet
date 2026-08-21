# CampNet

CampNet creates reproducible cellular-connectivity field surveys for campers,
RVers, and remote workers.

> CampNet measures what the modem observes—not just what the carrier
> advertises.

The project is an early working prototype. It can collect live Quectel modem
data through a GL.iNet router, preserve raw responses, parse radio data,
temporarily enable GNSS for one-off surveys, and run configurable router- or
collector-side speed tests.

## Quick start

```powershell
.\.venv\Scripts\python.exe -m campnet collect `
  --campground "Petoskey State Park" `
  --site "30"
.\.venv\Scripts\python.exe -m campnet show surveys\<survey-file>.json
```

Browse saved surveys interactively by location, site, and scan date:

```powershell
# Open the numbered console survey browser without remembering file names.
.\review-surveys.ps1
```

The equivalent direct command is `.\.venv\Scripts\python.exe -m campnet review`.
Historical JSON is not rewritten: it is reparsed using the latest reporting
logic. Carrier comparisons appear only when the stored scan contains usable
`+QSCAN:` cell rows with PLMN and RSRP measurements.

Replay the checked-in modem fixture through the AT provider:

```powershell
.\.venv\Scripts\python.exe -m campnet collect `
  --at-fixture tests\fixtures\quectel_basic.json `
  --profile continuous `
  --output surveys\fixture-survey.json
```

Collect live read-only modem observations through a configured router:

```powershell
Copy-Item devices.example.toml devices.toml
.\.venv\Scripts\python.exe -m campnet collect --device gl-x3000
```

The live transport uses OpenSSH batch mode and GL.iNet's `gl_modem` helper.

AT commands are defined once in `campnet.at_registry`. The generated
[command reference](docs/at-command-reference.md) documents their purpose,
safety, timeouts, parsers, and expected response families. Regenerate it with
`python -m campnet.at_docs` after reviewing a registry change.
It does not accept or persist passwords, passphrases, or private keys.
Collection prints a human-readable report and saves the complete versioned
survey, including raw responses, beneath the ignored `surveys/` directory.
The default `one-off` profile includes slow `COPS` and `QSCAN` discovery,
temporary GNSS enablement, and automatic sequential collection of both SIMs
when the modem explicitly reports both slots populated. CampNet restores GNSS
and the originally selected SIM afterward. It does not run a speed test.

Use `--profile continuous` for fast sampling without slow discovery, GNSS
state changes, SIM switching, or load tests. If GNSS is already enabled,
continuous mode makes one location query but never enables or disables it. Use `--optimize` when
diagnosing an existing active connection; that profile captures active radio
and configuration data and runs the configured speed test. Add
`--no-speed-test` to optimize without load, or `--no-gps` to omit GNSS from a
one-off survey.

`devices.toml` is local and Git-ignored. Device profiles select a known
transport and speed-test adapter; they cannot inject arbitrary remote command
arguments. For router-side tests, CampNet verifies the configured default-route
interface before starting and can fall back to the collector client.

Use `--output` to choose a specific JSON path. A comprehensive one-off survey
may temporarily enable GNSS and restores it afterward; continuous collection
does not change GNSS state.

See [CampNet_Development_Spec.md](CampNet_Development_Spec.md) for the living
product and engineering specification.

Accepted engineering constraints are indexed in
[decisions/README.md](decisions/README.md). Decision records are authoritative;
GitHub proposal issues are optional when research or discussion would help.

See [docs/hardware-baseline.md](docs/hardware-baseline.md) for the tested router,
modem, firmware, transport, and environment-specific observations.

Router authentication is intentionally handled outside CampNet. See
[docs/development.md](docs/development.md) for the key-based OpenWrt SSH setup.

## Sensitive survey data

Live surveys, captures, and raw-response directories are ignored by Git.
Never force-add field data. Only deliberately redacted modem responses belong
in `tests/fixtures/`; use `tests/fixtures/private/` for local, unredacted test
captures that must remain untracked.
