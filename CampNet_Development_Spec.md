# CampNet Development Specification

## Vision

CampNet is a field survey tool for cellular connectivity, designed for
campers, RVers, and remote workers. It gathers modem diagnostics, radio
measurements, GNSS location, and performance data into a reusable survey
that can be compared over time.

## Guiding Principles

1.  Preserve all raw modem responses.
2.  Parse raw responses into structured models.
3.  Generate all reports from the structured models.
4.  Version both the application and survey schema.
5.  Favor additive changes over breaking changes.
6.  Write regression tests using captured modem responses.
7.  Keep collection mechanisms behind provider interfaces.
8.  Treat the Survey model as the canonical boundary between collection,
    analysis, storage, and reporting.
9.  Treat the structured AT command registry as the authoritative reference
    for every AT command CampNet implements.

------------------------------------------------------------------------

# Product Positioning

CampNet is not a connection manager or a replacement for OpenWrt networking
tools. Existing tools such as ModemManager, `uqmi`, `umbim`, `qmicli`, and
LuCI modem applications are useful data sources, but they do not provide the
complete CampNet workflow: reproducible surveys, raw-response preservation,
cross-provider normalization, recommendations, reports, and historical
campground or campsite comparisons.

CampNet measures what the modem observes, not only what a carrier advertises.
Its primary long-term differentiator is history: comparing locations,
carriers, equipment, radio conditions, and performance over time.

------------------------------------------------------------------------

# Architecture

CampNet uses a provider-oriented collection architecture:

```text
Providers -> Survey (canonical model) -> Analyzers -> Reports / Storage / History
```

Each provider implements a small collection contract and contributes one or
more observations to a survey. Planned providers include AT, QMI, MBIM,
ModemManager, GL.iNet, speed-test, GNSS, weather, and tower-lookup providers.

Provider-specific payloads and errors must be retained as raw observations.
The rest of CampNet must not depend on the command or protocol used to obtain
the data. Supporting a new modem or transport should normally require a new
provider or parser, not changes to the Survey model, analyzers, or reports.

Providers may be unavailable on a particular system. A provider failure must
be recorded without discarding successful observations from other providers.
Providers that change modem state, including enabling GNSS or changing radio
configuration, require explicit user authorization.

## AT Command Tracking and Documentation

`campnet.at_registry` is the living, searchable source of truth for AT command
metadata. Runtime command lists reference stable registry identifiers rather
than duplicating command strings. `python -m campnet.at_docs` generates
`docs/at-command-reference.md`; generated documentation must contain every
registered command and must not be edited independently.

Each command definition records its identifier, exact command or safe
template, category, summary, project purpose, command type, parameters,
general expected response, sanitized examples, parser, side effects,
execution characteristics, prerequisites, related commands, references,
firmware and transport notes, and safety classification. Expected responses
describe a response family and never imply that one captured response applies
to every modem or firmware.

Safety classifications are read-only, low-risk configuration,
connectivity-impacting, persistent configuration, destructive, and unknown.
The executor must require explicit authorization before executing a command
classified as connectivity-impacting, persistent, destructive, or unknown.
Configuration operations must be restored when their registry entry requires
restoration. Session-dependent sequences remain a single registered batch
when the transport creates a fresh modem session per invocation.

Validation records are separate from command definitions. A record contains
the command identifier and timestamp; modem, firmware, router, operating
system, transport and transport arguments; relevant carrier, RAT, and
registration state; exact command, raw response, normalized result, duration,
status, and tester notes. Status is one of `documented`, `untested`,
`supported`, `supported_with_quirks`, `unsupported`, `timed_out`,
`inconclusive`, or `dangerous_not_tested`. A failure describes only its tested
environment and must not make a command globally unsupported.

Validation reports keep four concepts distinct: documented behavior from an
authoritative reference; observed behavior from a specific run; the project's
current interpretation; and unresolved open questions. In particular,
behavior that changes between separate `gl_modem` invocations is recorded as
transport-observed behavior until modem persistence is independently proven.

Diagnostic logging, when enabled, records timestamp, command identifier,
redacted rendered command, transport, timeout, raw response, parsed response,
duration, and error classification. It supports human-readable output and
JSON Lines. Redaction must cover IMEI, ICCID, IMSI, phone numbers, coordinates,
message contents, authentication material, and APN credentials before logs or
fixtures leave private survey storage.

Exact modem failures (`ERROR`, `+CME ERROR`, and `+CMS ERROR`) are preserved
before normalization. The normalized error record stores error family,
optional numeric code, raw text, command identifier, transport, cautious
human interpretation with confidence, and suggested diagnostics. Timeouts,
transport failures, malformed responses, and parser failures remain distinct.

Every shell or AT example has concise comments immediately above it explaining
what is run, why, important parameters, expected high-level output, and any
material side effect. Comments must add meaning rather than repeat a command.

To add a command: add and review its registry definition, link its parser,
add sanitized response fixtures, add or update integrity/parser tests,
regenerate the reference, and record each real validation environment
separately. Unsupported assumptions remain `untested` or `inconclusive` until
evidence supports a stronger status. This work does not expand SMS features.

------------------------------------------------------------------------

# Phase 0 -- Bootstrap

The development agent should first verify:

-   Python 3.11+ installed
-   Git installed
-   GitHub authentication configured
-   Repository cloned and writable
-   Virtual environment created
-   Project opens successfully in the desktop client
-   Linting and formatting configured
-   Unit tests runnable

Suggested tooling:

-   Python
-   pytest
-   ruff
-   black
-   mypy
-   pre-commit

------------------------------------------------------------------------

# Repository Layout

``` text
campnet/
├── README.md
├── CHANGELOG.md
├── ROADMAP.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── docs/
│   ├── architecture.md
│   ├── schema.md
│   ├── modem-notes.md
│   └── development.md
├── tests/
│   ├── fixtures/
│   └── test_parsers.py
├── samples/
│   └── surveys/
├── campnet/
│   ├── __init__.py
│   ├── cli.py
│   ├── modem.py
│   ├── parser.py
│   ├── models.py
│   ├── analyzer.py
│   ├── reports.py
│   ├── exporters.py
│   ├── speedtest.py
│   ├── gnss.py
│   └── history.py
└── scripts/
```

------------------------------------------------------------------------

# Milestones

## M1 -- Collection

-   Provider contract and collection orchestration
-   Robust AT transport
-   MHI and ttyUSB support
-   Retries
-   Timeouts
-   Logging
-   Raw response capture

Commands:

-   ATI
-   AT+QNWINFO
-   AT+QENG="servingcell"
-   AT+QENG="neighbourcell"
-   AT+QCAINFO
-   AT+COPS=?
-   AT+QSCAN=1
-   AT+QGPS?
-   AT+QGPSLOC?

## M2 -- Parsing

Models:

-   Survey
-   Metadata
-   ModemInfo
-   ServingCell
-   NeighborCell
-   VisibleCell
-   CarrierAggregation
-   GPSLocation
-   SpeedTestResult
-   Recommendation

## M3 -- Analysis

Produce:

-   Signal quality
-   Carrier ranking
-   Band recommendations
-   Congestion indicators
-   Upload vs download guidance
-   Human-readable recommendations

## M4 -- Reporting

Outputs:

-   Console
-   Markdown
-   HTML
-   JSON
-   CSV

## M5 -- History

-   Compare surveys
-   Historical trends
-   Campground summaries
-   Site comparisons

------------------------------------------------------------------------

# Survey Schema

Survey

-   survey_id (UUID)
-   schema_version
-   app_version
-   timestamp
-   metadata
-   modem
-   location
-   serving_cell
-   neighbor_cells
-   visible_cells
-   carrier_aggregation
-   speedtest
-   recommendations
-   raw_responses

Raw responses must always be retained.

Every survey also records provider outcomes, including provider name,
collection timestamp, raw payloads, and non-fatal errors. The schema must
allow additive provider data without coupling the canonical model to one
modem family or transport.

------------------------------------------------------------------------

# Metadata

Capture:

-   Campground
-   Site
-   Notes
-   Weather (future)
-   Router placement
-   Antenna configuration
-   Power source
-   User observations

------------------------------------------------------------------------

# GNSS

Collect when enabled:

-   Latitude
-   Longitude
-   Altitude
-   UTC
-   Speed
-   Heading
-   HDOP

Do not automatically enable GNSS unless explicitly requested.

For explicitly requested comprehensive one-off surveys, CampNet may
temporarily enable GNSS, attempt to obtain a fix, and then restore the prior
GNSS state. Continuous surveys must not repeatedly enable or disable GNSS.

------------------------------------------------------------------------

# Collection Profiles

One-off manual surveys prioritize completeness and include slow operator and
visible-cell scans (`AT+COPS=?` and `AT+QSCAN=1`) by default. Continuous or
movement-oriented surveys prioritize sampling cadence and omit those slow
scans. Both profiles preserve every response and record partial failures.

One-off surveys also capture the current RAT acquisition order and LTE, NSA
5G, and SA 5G band preferences. These values form an immutable pre-test
configuration snapshot. Future band-lock experiments must construct their
restore operation from that snapshot, verify every write response, re-query
the settings after restoration, and record both before and after states.

------------------------------------------------------------------------

# Speed Tests

Auto-detect supported CLI.

Comprehensive one-off surveys run a speed test by default when a supported
client is available. Continuous surveys omit speed tests. Users must be able
to disable a one-off speed test on metered connections.

Collect:

-   Download
-   Upload
-   Latency
-   Jitter
-   Packet loss (when available)

Store normalized measurements in the canonical survey and preserve the raw
client result. Record whether the test executed on the collector computer or
router because results represent the modem path only when traffic is routed
through that modem.

The survey UUID is the stable join key for exports and related datasets.
Provider results collected as part of a one-off survey remain embedded in that
survey. Future continuous sessions may use the survey UUID as a parent/session
identifier while assigning individual sample identifiers and timestamps.

Speed-test execution is configured per device. A device profile records the
transport, SSH endpoint, modem bus, known speed-test adapter, executable,
expected default-route interface, timeout, and fallback policy. Configuration
selects only built-in safe adapters and must not supply arbitrary shell
commands. Local device profiles are not committed; a sanitized example is.

------------------------------------------------------------------------

# Recommendations

Examples:

-   Automatic mode recommended.
-   Band 14 offers better upload.
-   Band 12 has strongest signal but lowest throughput.
-   Likely tower congestion.
-   Consider router repositioning.

------------------------------------------------------------------------

# Regression Tests

Create fixtures from real modem captures.

Fixtures must be replayable through the same provider interface used by live
transports. Secrets and identifiers such as IMEI, IMSI, ICCID, Wi-Fi keys,
public IP addresses, and precise coordinates must be redacted before a capture
is committed.

Include:

-   QSCAN
-   QENG
-   QCAINFO
-   COPS
-   GNSS

Parser changes must pass all fixture tests.

------------------------------------------------------------------------

# Versioning

Application:

Semantic Versioning.

Examples:

-   0.1.0
-   0.2.0
-   1.0.0

Survey schema:

Independent integer version.

------------------------------------------------------------------------

# Git Workflow

-   main always releasable
-   feature branches
-   small commits
-   descriptive commit messages
-   PRs for major features
-   update CHANGELOG for user-visible changes

CHANGELOG should follow Keep a Changelog.

------------------------------------------------------------------------

# Initial Deliverables

1.  Working AT transport
2.  JSON survey generation
3.  Parser implementation
4.  Console report
5.  Unit tests
6.  Sample survey files
7.  Documentation

This document should be treated as the living product specification and
updated as requirements evolve through field testing.

For the tested hardware baseline, observed firmware behavior, machine-local
files, migration procedure, and prioritized continuation work, see
`docs/project-handoff.md`. Those observations are evidence for a specific
environment; they do not become universal modem assumptions.
