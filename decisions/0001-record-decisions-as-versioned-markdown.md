---
id: DEC-0001
title: Record decisions as versioned Markdown
status: accepted
date: 2026-08-21
type: engineering
scope:
  - repository-wide
owners:
  - project-maintainer
supersedes: []
superseded_by: null
discussion: null
---

# DEC-0001: Record decisions as versioned Markdown

## Problem statement

Engineering choices embedded only in specifications, code, or conversations
are difficult for people and coding agents to discover and apply consistently.
CampNet needs a durable, reviewable source of binding engineering direction
without making lightweight solo development burdensome.

## Decision

Store accepted engineering decisions as versioned Markdown in `decisions/`
and maintain an index in `decisions/README.md`. Only accepted, non-deprecated,
non-superseded records are active direction.

Decision records must stand alone with sufficient context, rationale, and
consequences. GitHub issues are optional deliberation tools: use them when
research or discussion benefits from an issue, and link them when they exist.
An issue is not a prerequisite for an accepted decision.

## Consequences and follow-up

Contributors and coding agents must read applicable accepted decisions before
changing code and cite them in pull requests. Changes in direction require a
new record that explicitly supersedes the prior record. Review the workflow
after the first five post-bootstrap decisions and remove any fields that create
more overhead than value.

## Alternatives considered

- Require a proposal issue for every decision: rejected because it creates
  duplicate tracking for decisions made by a solo maintainer.
- Keep decisions only in issues or conversations: rejected because they do not
  provide a compact, versioned source of binding direction beside the code.
