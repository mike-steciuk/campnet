# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

- Recognize the extended dual-SIM inventory returned by GL-X3000 RM520N firmware,
  while keeping ambiguous slot responses in the safe unknown state.
- Fixed multi-SIM parent normalization so shared passive carrier scans remain
  available to reports, including in-memory recovery for already-saved scans.
- Added an operation-specific one-off preflight with safe cancellation and
  `--yes` automation support before long scans, GNSS changes, or SIM switching.
- Moved Quectel parsing to collection/schema-read normalization so reports
  consume canonical structured radio observations while raw evidence remains
  available.
- Routed future configuration restoration through parameterized AT registry
  operations and classified long operator scans by connectivity impact.
- Preserved structured stdout, stderr, exit status, and timeout evidence from
  failed speed-test and SSH AT executions.
- Separate generic multi-SIM orchestration from vendor-specific slot control
  and Quectel response parsing, with an extension contract for new devices.

- Documented the sequential multi-SIM survey model, privacy boundaries,
  switching safety, and phased implementation plan.
- Added conservative dual-SIM detection, sequential active-radio collection,
  mandatory original-slot restoration, and an `optimize`-only speed-test profile.
- Added per-slot multi-SIM reporting; live two-SIM validation remains pending.
- Continuous surveys now record an existing GNSS fix with one query while
  leaving disabled receivers and acquisition state unchanged.
- Labeled carrier-aggregation results with the registered carrier and PLMN,
  with an explicit unknown fallback when attribution is ambiguous.
- Added an interactive console survey browser organized by location, site,
  and reverse-chronological scan date, plus a PowerShell launcher.
- Added ranked per-carrier signal reporting from passive visible-cell scans,
  including quality, detected-cell counts, and explicit coverage caveats.
- Replaced transient handoff state with durable setup and tested-hardware
  documentation.
- Added an authoritative AT command registry, typed validation and error
  records, safety guards, generated reference documentation, and registry
  integrity tests.

### Added

- Provider-oriented collection architecture.
- Versioned canonical Survey model and JSON persistence.
- Initial command-line interface and test suite.
- Retrying transport-independent AT client and provider.
- Replay transport with a captured-style Quectel modem fixture.
- Secure OpenWrt SSH onboarding guidance.
- Live key-authenticated SSH transport for GL.iNet `gl_modem` collection.
- Quectel RM520N parsers for modem identity, registration, serving and
  neighboring cells, and carrier aggregation.
- Human-readable radio report with conservative signal interpretation.
- Default comprehensive one-off profile with COPS and QSCAN carrier discovery.
- Lightweight continuous profile that omits slow network scans.
- Reversible GNSS collection that restores the modem's prior GNSS state.
- Extended carrier report grouped by operator and strongest observed LTE cell.
- Read-only RAT and LTE/5G band-preference snapshots for future safe restoration.
- Stable UUID identity for every survey with backward-compatible legacy loading.
- Auto-detected Ookla and speedtest-cli performance provider with raw JSON retention.
- Validated per-device TOML profiles and router-executed speed tests with route checks.
