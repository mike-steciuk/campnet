---
id: DEC-0003
title: Use normalized Survey data as the reporting boundary
status: accepted
date: 2026-08-21
type: architecture
scope:
  - survey
  - providers
  - parsing
  - reporting
owners:
  - project-maintainer
supersedes: []
superseded_by: null
discussion: null
---

# DEC-0003: Use normalized Survey data as the reporting boundary

## Problem statement

CampNet must support multiple modem families and collection mechanisms without
coupling reports and analyzers to provider protocols. The current report path
reparses raw AT responses with a Quectel-specific parser, despite the Survey
being intended as the canonical boundary.

## Decision

Providers and their parsers produce normalized structured observations in the
canonical `Survey`. Reports, analyzers, storage consumers, and history features
consume those normalized observations and must not depend on a modem command,
transport, or provider-specific response format.

Raw responses remain stored alongside normalized observations for audit,
diagnostics, and deliberate reprocessing; they are not the normal reporting
interface.

## Consequences and follow-up

Move Quectel parsing out of `report.py` and into the provider/parsing stage.
Define additive normalized observation structures that permit new providers
without requiring provider-specific report branches. Existing report-time
parsing is recognized migration debt and may remain temporarily while the
normalized schema is introduced and tested.

## Alternatives considered

- Reparse raw responses whenever a report is generated: rejected because it
  couples consumers to providers and lets reports change historical meaning
  silently as parsers evolve.
