---
id: DEC-0004
title: Route executable AT operations through the registry
status: accepted
date: 2026-08-21
type: architecture
scope:
  - AT-registry
  - AT-execution
  - configuration-restoration
owners:
  - project-maintainer
supersedes: []
superseded_by: null
discussion: null
---

# DEC-0004: Route executable AT operations through the registry

## Problem statement

Safety, documentation, authorization, timeouts, parsing, and restoration depend
on complete command metadata. Independently constructed executable strings can
bypass those controls. The current restoration planner constructs future
`AT+QNWPREFCFG` writes outside the registry.

## Decision

Every executable AT operation—including parameterized writes and restoration
commands—must be defined and rendered through the AT registry. Planning code
returns stable registry identifiers and validated parameters, never
independently constructed executable AT strings.

## Consequences and follow-up

Add parameterized registry definitions for configuration writes before band
experiments can execute. Refactor `campnet/configuration.py` to return planned
registry operations rather than strings. Generated documentation, safety
checks, authorization, and integrity tests then cover both forward and restore
operations. The present string-building helper is migration debt and must not
be connected to execution unchanged.

## Alternatives considered

- Permit locally validated command construction: rejected because validation
  alone does not attach the registry's safety and operational metadata.
