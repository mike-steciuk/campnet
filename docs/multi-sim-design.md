# Multi-SIM Survey Design

## Hardware constraint

The GL.iNet GL-X3000 is dual-SIM, single-standby hardware. Two cards can be
installed, but only one is active at a time. Switching interrupts cellular
service and may take approximately one minute. Quectel documents
`AT+QUIMSLOT?` for querying the active slot and `AT+QUIMSLOT=<slot>` for
changing it; selection takes effect immediately and is saved.

CampNet must treat multi-SIM collection as a controlled sequence of single-SIM
observations, not simultaneous measurement.

## Architecture and extension contract

The implementation separates workflow from device syntax:

```text
MultiSIMProvider (generic orchestration)
  -> SIMSlotController (hardware-neutral protocol)
       -> QuectelATSimSlotController (vendor adapter and parsers)
  -> shared DataProvider (passive scans once)
  -> segment DataProvider (active-radio observations per slot)
```

`campnet/sim.py` defines immutable `SIMInventory`, `SIMSelection`, and
`SIMState` results plus the `SIMSlotController` protocol. Every result carries
raw responses and errors as evidence. `campnet/providers/multisim.py` only
understands slot IDs and provider results. It iterates any number of slots and
restores the initially active slot in `finally`. The current GL-X3000 adapter
in `campnet/providers/quectel_sim.py` happens to parse a two-slot Quectel
response; that hardware limit is not part of the generic contract.

A new device adapter must implement:

```python
inventory() -> SIMInventory       # active slot plus installed slot IDs
state(slot) -> SIMState           # immediate SIM and registration state
select(slot) -> SIMSelection      # mutate, re-query, and verify selection
wait_until_ready(slot) -> SIMState  # bounded readiness/registration polling
```

Parsers stay beside the vendor adapter and are pure, conservative functions.
Unknown or malformed output produces unknown/empty results and never guesses
that a slot exists or that a mutation succeeded. The adapter owns command
authorization, timeouts, polling, and exact raw/error capture. The orchestrator
owns ordering, segment failure isolation, and mandatory restoration; report
parsers consume only the normalized provider result.

Integration checklist for another modem family:

1. Add read and switch commands to the AT registry with correct safety,
   persistence, timeout, and restoration metadata.
2. Implement a vendor-specific `SIMSlotController`; do not add vendor branches
   to `MultiSIMProvider`.
3. Add sanitized fixtures for normal, single-slot, partial, malformed, and
   unsupported responses, plus failed write and failed verification cases.
4. Reuse or add `DataProvider` implementations for shared and active-slot data.
5. Wire the adapter in device construction/configuration and document any
   router auto-switch, APN, or reboot behavior.
6. Field-test discovery, every switch, registration timeout, and restoration;
   record mock-tested and hardware-validated claims separately.

## What current surveys already do

With one active SIM, a comprehensive one-off survey has two kinds of data:

1. Passive/environment observations: operator discovery (`AT+COPS=?`),
   carrier-attributed visible cells (`AT+QSCAN=1`), GNSS, and device context.
2. Active-SIM observations: registered PLMN/RAT, serving and neighboring cells,
   carrier aggregation, and registration state.

The passive scan may already identify both SIM providers and compare their
strongest detected RSRP without switching cards. It cannot establish whether
the inactive SIM can register, which bands it will use, its aggregation,
APN/data-session behavior, or its speed and latency.

## Proposed collection model

A multi-SIM run creates one parent survey session with one or more SIM-slot
segments. The parent owns shared context; each segment owns observations made
while that slot was active.

```text
MultiSimSurveySession
  session_id, timestamp, location, device, antenna, placement
  shared passive scan and GNSS context
  original_active_slot
  segments[]
    segment_id, sim_slot, safe SIM label/identity
    observed registered PLMN/carrier
    SIM readiness and registration state
    serving/neighbor/aggregation observations
    raw responses, timings, and errors
  restoration result
```

ICCID and IMSI must not appear unredacted in reports, committed fixtures, or
diagnostic logs. Prefer a configured label such as `primary` or a stable local
salted identifier.

## Collection sequence

1. Record the original active slot, SIM readiness, registration, APN/profile
   context, and router auto-switch policy.
2. Collect shared location and an initial passive carrier scan.
3. For each authorized slot:
   1. Select it only if it is not already active.
   2. Wait for SIM readiness and registration with bounded timeouts, recording
      every transition.
   3. Record safe SIM identity, registered PLMN, serving cells, neighbors,
      aggregation, and relevant configuration.
   4. Record why registration was skipped; one slot's failure
      must not discard another segment.
   5. Optionally repeat passive scans per slot to reveal SIM/firmware bias.
4. Restore the original slot and router auto-switch policy in a `finally` path,
   wait for the original connection, then re-query and retain restoration proof.

## Recommended defaults

- Run one initial `COPS`/`QSCAN` passive baseline.
- Run one full active-SIM subset per selected installed slot.
- Offer `--scan-each-sim` to repeat slow passive scans after each switch.
- Restore the original slot unless the user explicitly chooses another final
  slot.
- Never cycle slots automatically during continuous/moving collection.
- Never run a load test during the one-off multi-SIM workflow.

Speed tests belong only to `--optimize`. Optimize measures the current
active connection and does not switch SIMs automatically. To optimize two SIMs,
select each desired SIM as the active connection and run a separate optimize
survey after it has registered and established a data route.

## Configuration direction

```toml
[devices.gl-x3000.multi_sim]
enabled = true
switch_adapter = "glinet"
registration_timeout_seconds = 120
restore_original_slot = true
scan_each_sim = false

[[devices.gl-x3000.sim_slots]]
slot = 1
label = "primary"
expected_carrier = "AT&T"

[[devices.gl-x3000.sim_slots]]
slot = 2
label = "backup"
expected_carrier = "T-Mobile"
```

Expected carrier is a validation hint, not an identity assertion. Observed
registered PLMN remains authoritative for the segment.

## Implementation phases

1. Add non-mutating active-slot, SIM readiness, redacted identity,
   registration, and route inventory commands and validation records.
2. Add the parent/segment schema and reports using replay fixtures without live
   switching.
3. Validate the GL.iNet firmware's switch path and its interaction with router
   auto-switch and per-SIM APN profiles.
4. Add an explicitly authorized executor with restoration guarantees.
5. Add comparison reports, failure isolation, and field validation using two
   activated SIMs. Keep throughput testing in separate optimize surveys.

The switch orchestration is implemented and covered by a stateful mock
transport. Live two-SIM behavior remains unvalidated until a second activated
SIM is available. Until then, treat the dual-slot response parser, GL.iNet
auto-connect/APN interaction, registration timing, and restoration as field
validation requirements rather than proven behavior.
