---
id: DEC-0006
title: Keep released survey schemas backward readable
status: accepted
date: 2026-08-21
type: architecture
scope:
  - survey-schema
  - storage
  - history
owners:
  - project-maintainer
supersedes: []
superseded_by: null
discussion: null
---

# DEC-0006: Keep released survey schemas backward readable

## Problem statement

Historical comparison is a core CampNet capability. The current loader accepts
only the current schema version, which is sufficient while version 1 is the
only release but would reject historical surveys after a simple version bump.

## Decision

CampNet must continue reading every released survey-schema version. Readers use
explicit, tested migrations to produce the current normalized in-memory model.
Schema changes should be additive when practical. Reading or migrating must
never silently rewrite the original stored survey document.

## Consequences and follow-up

The strict version-1 loader is acceptable while version 1 is the only released
schema. Before releasing schema version 2, add a version-dispatch and migration
path with fixtures for every supported historical version. Preserve unknown
raw provider evidence even when an older normalized field has no current
equivalent.

## Alternatives considered

- Support only the latest schema: rejected because it conflicts with durable
  field evidence and historical comparison.
- Rewrite stored surveys in place: rejected because it destroys provenance and
  makes migrations difficult to audit or repeat.
