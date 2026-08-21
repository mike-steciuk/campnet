# Instructions for coding agents

CampNet's accepted decision records are binding engineering constraints.

Before planning or changing code:

1. Read `decisions/README.md`.
2. Read every accepted decision whose scope applies to the requested work.
3. Follow those decisions even when another implementation seems preferable.
4. Do not treat deprecated or superseded records as current direction.
5. If a request conflicts with an accepted decision, stop and report the
   decision ID, the conflict, and the smallest viable resolution.
6. Do not silently replace or weaken a decision. Add a new decision record
   that explicitly supersedes the old one.
7. In pull requests, list applied decision IDs under `Decisions applied`.

When a decision is ambiguous, preserve existing behavior and ask for
clarification. Instructions closer to changed code may add constraints but may
not override an accepted decision unless that decision explicitly allows it.
