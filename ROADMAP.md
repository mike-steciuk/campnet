# Roadmap

Status reflects the implementation as of 2026-08-15. Checked items are
implemented in the current feature branch; they may still need field hardening.

## 0.1 - Foundation

- [x] Canonical Survey schema with UUID identity
- [x] Provider contract and collection orchestration
- [x] JSON persistence and CLI
- [x] Captured-response fixture strategy
- [x] Sensitive survey and local device configuration exclusions

## 0.2 - Modem collection

- [x] SSH/GL.iNet AT transport with retries and timeouts
- [x] Quectel response capture and parsers
- [x] Serving, neighboring, carrier-aggregation, and visible-cell data
- [x] Reversible one-off GNSS provider
- [x] Band and RAT preference snapshots
- [x] Authoritative AT command registry and generated reference
- [ ] Persist structured validation records from live command executions
- [ ] Add direct serial/MHI and QMI/MBIM transports where useful

## 0.3 - Performance, analysis, and reporting

- [x] Conservative signal-quality analysis
- [x] Human-readable console report
- [x] Configurable router/collector `speedtest-cli` integration
- [x] Passive per-carrier signal comparison from visible-cell scans
- [x] Interactive local survey browser by location, site, and scan date
- [ ] Diagnose and harden Speedtest.net HTTP 429 behavior
- [ ] Add an alternative router-side test adapter such as LibreSpeed
- [ ] Markdown report/export
- [ ] Correlate performance with cells, bands, configuration, and location
- [ ] Actionable carrier, placement, antenna, and congestion recommendations

## 0.4 - Continuous collection and history

- [ ] Define continuous-session/sample schema and safe sampling cadence
- [ ] Campground and campsite comparisons
- [ ] Carrier and equipment trends
- [ ] CSV and HTML exports
- [ ] Map and time-series views with coordinate privacy controls

## 0.5 - Multi-SIM surveys

- [x] Read-only active-slot, SIM readiness, and registration inventory
- [x] Provider-level parent result with per-SIM-slot observation segments
- [ ] Redacted/stable local SIM identity and configured safe slot labels
- [ ] Explicitly authorized GL-X3000 slot switching with verified restoration
- [x] Mocked sequential per-SIM radio collection with original-slot restoration
- [ ] Live validation with two installed and activated SIMs
- [ ] Optional repeated passive scans to measure SIM/firmware scan bias
- [ ] Side-by-side per-SIM coverage, aggregation, and performance reporting

## Later

- [ ] Controlled band experiments with snapshot, explicit authorization,
  restoration, and verification
- [ ] Additional modem and router device profiles
- [ ] Packaging and installation workflow for collector computers
- [ ] Automated redaction tooling for shareable fixtures and diagnostics
