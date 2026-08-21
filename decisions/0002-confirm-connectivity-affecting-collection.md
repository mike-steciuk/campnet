---
id: DEC-0002
title: Confirm connectivity-affecting collection
status: accepted
date: 2026-08-21
type: safety
scope:
  - collection
  - command-line-interface
owners:
  - project-maintainer
supersedes: []
superseded_by: null
discussion: null
---

# DEC-0002: Confirm connectivity-affecting collection

## Problem statement

The one-off collection profile may run long scans and temporarily enable GNSS.
Invoking `collect` expresses intent to run the selected profile, but users
should understand planned state changes and possible connectivity effects
before they occur. Automation must remain possible without an interactive
prompt.

## Decision

Invoking `collect` authorizes the operations belonging to its selected
profile. Before executing an operation that changes modem state or may affect
connectivity, CampNet must display an operation-specific preflight warning and
require confirmation.

Interactive confirmation defaults to cancellation. `--yes` provides explicit
non-interactive confirmation. Options such as `--no-gps` remove the associated
operation and warning. When confirmation is unavailable, CampNet must cancel
before performing affected operations. Continuous collection remains
non-disruptive and does not prompt.

## Consequences and follow-up

Add preflight planning and confirmation to the CLI before expanding
state-changing or connectivity-impacting collection. Warnings must name the
planned operations, likely effects, and restoration behavior rather than use a
generic danger message. The existing one-off flow lacks this confirmation and
is migration debt.

## Alternatives considered

- Treat the command invocation alone as sufficient notice: rejected because it
  does not make profile side effects visible at execution time.
- Require a separate affirmative flag for every low-risk operation: rejected
  as unnecessary friction when a single accurate preflight can cover the plan.
