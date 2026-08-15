# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

- Added an interactive console survey browser organized by location, site,
  and reverse-chronological scan date, plus a PowerShell launcher.
- Added ranked per-carrier signal reporting from passive visible-cell scans,
  including quality, detected-cell counts, and explicit coverage caveats.
- Updated roadmap, setup guidance, and durable handoff context for moving
  development to another computer.
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
