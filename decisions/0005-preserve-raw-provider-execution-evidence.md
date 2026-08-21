---
id: DEC-0005
title: Preserve raw provider execution evidence
status: accepted
date: 2026-08-21
type: engineering
scope:
  - providers
  - transports
  - survey-storage
owners:
  - project-maintainer
supersedes: []
superseded_by: null
discussion: null
---

# DEC-0005: Preserve raw provider execution evidence

## Problem statement

Failures are often the most valuable field evidence. Current failed speed-test
and SSH execution paths may retain only a summarized exception, losing complete
stdout, stderr, exit status, or partial timeout output needed for diagnosis.

## Decision

Every provider execution attempt preserves all available raw results regardless
of success, including stdout, stderr, exit status, timeout details, and
transport errors. Normalized errors remain distinct from raw evidence so that
reports can be concise without discarding diagnostic facts.

Sensitive raw evidence remains in protected survey storage. It must be
redacted before it is committed, shared, logged outside that boundary, or used
as a public fixture.

## Consequences and follow-up

Introduce structured execution results that adapters can return for success,
nonzero exit, malformed output, and timeout cases. Update providers to persist
attempt evidence while producing cautious normalized errors. Existing failure
paths that collapse output into exception text are migration debt.

## Alternatives considered

- Store exception messages only: rejected because formatting an error is a
  lossy interpretation and cannot support later diagnosis or reprocessing.
