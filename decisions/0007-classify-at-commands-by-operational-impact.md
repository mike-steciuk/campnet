---
id: DEC-0007
title: Classify AT commands by operational impact
status: accepted
date: 2026-08-21
type: safety
scope:
  - AT-registry
  - authorization
owners:
  - project-maintainer
supersedes: []
superseded_by: null
discussion: null
---

# DEC-0007: Classify AT commands by operational impact

## Problem statement

A syntactically read-only query can still interrupt service, monopolize the
modem, or take several minutes. `AT+COPS=?` is currently classified read-only
even though its registry entry warns that the scan may temporarily affect
connectivity, so safety enforcement does not reflect its documented impact.

## Decision

AT-command safety classification reflects operational impact, not merely
whether a command writes persistent configuration. Any command that may
interrupt, degrade, or monopolize connectivity is connectivity-impacting and
requires the corresponding authorization and preflight warning, even when it
is syntactically a query.

`network.operator_scan` is connectivity-impacting. Commands with insufficient
evidence for a reliable classification remain unknown and receive guarded
treatment until validated.

## Consequences and follow-up

Reclassify `network.operator_scan`, update generated documentation and tests,
and include the long scan in the one-off preflight described by DEC-0002.
Review other long-running commands using documented and observed behavior
rather than assuming that query syntax makes them operationally harmless.

## Alternatives considered

- Classify only persistent writes as risky: rejected because it ignores
  temporary service disruption.
- Add a separate disruptive-read category immediately: deferred until actual
  use shows that it improves behavior beyond the existing guarded class.
