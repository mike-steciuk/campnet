# CampNet AT Command Reference

Generated from `campnet.at_registry`; do not edit by hand.

## `config.lte_bands`

- Command: `AT+QNWPREFCFG="lte_band"`
- Category: configuration
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Queries enabled LTE bands.

Purpose: Snapshots configuration for later restoration.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Queries enabled LTE bands.
# Snapshots configuration for later restoration.
gl_modem -B 1-1.2 AT 'AT+QNWPREFCFG="lte_band"'
```

## `config.mode_preference`

- Command: `AT+QNWPREFCFG="mode_pref"`
- Category: configuration
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Queries the radio mode preference.

Purpose: Snapshots configuration for later restoration.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Queries the radio mode preference.
# Snapshots configuration for later restoration.
gl_modem -B 1-1.2 AT 'AT+QNWPREFCFG="mode_pref"'
```

## `config.nr_mode`

- Command: `AT+QNWPREFCFG="nr5g_disable_mode"`
- Category: configuration
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Queries the NR disable mode.

Purpose: Snapshots configuration for later restoration.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Queries the NR disable mode.
# Snapshots configuration for later restoration.
gl_modem -B 1-1.2 AT 'AT+QNWPREFCFG="nr5g_disable_mode"'
```

## `config.nsa_bands`

- Command: `AT+QNWPREFCFG="nsa_nr5g_band"`
- Category: configuration
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Queries enabled NSA NR bands.

Purpose: Snapshots configuration for later restoration.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Queries enabled NSA NR bands.
# Snapshots configuration for later restoration.
gl_modem -B 1-1.2 AT 'AT+QNWPREFCFG="nsa_nr5g_band"'
```

## `config.rat_order`

- Command: `AT+QNWPREFCFG="rat_acq_order"`
- Category: configuration
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Queries radio-access acquisition order.

Purpose: Snapshots configuration for later restoration.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Queries radio-access acquisition order.
# Snapshots configuration for later restoration.
gl_modem -B 1-1.2 AT 'AT+QNWPREFCFG="rat_acq_order"'
```

## `config.sa_bands`

- Command: `AT+QNWPREFCFG="nr5g_band"`
- Category: configuration
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Queries enabled SA NR bands.

Purpose: Snapshots configuration for later restoration.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Queries enabled SA NR bands.
# Snapshots configuration for later restoration.
gl_modem -B 1-1.2 AT 'AT+QNWPREFCFG="nr5g_band"'
```

## `gnss.enable`

- Command: `AT+QGPS=1`
- Category: GPS/GNSS
- Type: set/configuration
- Safety: low-risk configuration
- Timeout: 10 seconds
- Parser: none

Starts the GNSS engine.

Purpose: Temporarily enables GNSS for an authorized one-off fix.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

Side effects:

- Changes GNSS state and requires restoration when CampNet enabled it.

```bash
# Starts the GNSS engine.
# Temporarily enables GNSS for an authorized one-off fix.
gl_modem -B 1-1.2 AT 'AT+QGPS=1'
```

## `gnss.location`

- Command: `AT+QGPSLOC=2`
- Category: GPS/GNSS
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.providers.gnss._parse_location`

Queries a GNSS fix in a structured format.

Purpose: Adds time, position, altitude, and motion to a survey.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Queries a GNSS fix in a structured format.
# Adds time, position, altitude, and motion to a survey.
gl_modem -B 1-1.2 AT 'AT+QGPSLOC=2'
```

## `gnss.state`

- Command: `AT+QGPS?`
- Category: GPS/GNSS
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.providers.gnss._gps_enabled`

Queries whether the GNSS engine is enabled.

Purpose: Prevents CampNet from overwriting pre-existing GNSS state.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Queries whether the GNSS engine is enabled.
# Prevents CampNet from overwriting pre-existing GNSS state.
gl_modem -B 1-1.2 AT 'AT+QGPS?'
```

## `gnss.stop`

- Command: `AT+QGPSEND`
- Category: GPS/GNSS
- Type: execution/action
- Safety: low-risk configuration
- Timeout: 10 seconds
- Parser: none

Stops the GNSS engine.

Purpose: Restores GNSS state after CampNet temporarily enabled it.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

Side effects:

- Changes GNSS state.

```bash
# Stops the GNSS engine.
# Restores GNSS state after CampNet temporarily enabled it.
gl_modem -B 1-1.2 AT 'AT+QGPSEND'
```

## `modem.identity`

- Command: `ATI`
- Category: modem identity
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Reports modem identity and revision.

Purpose: Identifies the modem and firmware associated with a survey.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Reports modem identity and revision.
# Identifies the modem and firmware associated with a survey.
gl_modem -B 1-1.2 AT 'ATI'
```

## `network.carrier_aggregation`

- Command: `AT+QCAINFO`
- Category: signal quality
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Reports active carrier aggregation components.

Purpose: Records primary and secondary carriers.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Reports active carrier aggregation components.
# Records primary and secondary carriers.
gl_modem -B 1-1.2 AT 'AT+QCAINFO'
```

## `network.cell_scan`

- Command: `AT+QSCAN=1`
- Category: operator scan
- Type: query
- Safety: read-only
- Timeout: 240 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Performs a detailed Quectel cell scan.

Purpose: Captures cells beyond the registered operator.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

Side effects:

- Long-running scan; partial output is firmware-dependent.

```bash
# Performs a detailed Quectel cell scan.
# Captures cells beyond the registered operator.
gl_modem -B 1-1.2 SAT sp AT+QSCAN=1
```

## `network.current`

- Command: `AT+QNWINFO`
- Category: network registration
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Reports current access technology, operator, band, and channel.

Purpose: Records the currently registered network.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Reports current access technology, operator, band, and channel.
# Records the currently registered network.
gl_modem -B 1-1.2 AT 'AT+QNWINFO'
```

## `network.eps_registration`

- Command: `AT+CEREG?`
- Category: network registration
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.providers.multisim.registration_ready`

Queries EPS registration state.

Purpose: Waits for home or roaming registration after a slot switch.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Queries EPS registration state.
# Waits for home or roaming registration after a slot switch.
gl_modem -B 1-1.2 AT 'AT+CEREG?'
```

## `network.neighbor_cells`

- Command: `AT+QENG="neighbourcell"`
- Category: neighboring cells
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Reports neighboring-cell engineering data.

Purpose: Captures alternatives visible to the modem.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Reports neighboring-cell engineering data.
# Captures alternatives visible to the modem.
gl_modem -B 1-1.2 AT 'AT+QENG="neighbourcell"'
```

## `network.operator_scan`

- Command: `AT+COPS=?`
- Category: operator scan
- Type: query
- Safety: read-only
- Timeout: 180 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Scans operators visible to the modem.

Purpose: Makes one-off surveys carrier-complete.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

Side effects:

- Long-running scan; may temporarily affect connectivity.

```bash
# Scans operators visible to the modem.
# Makes one-off surveys carrier-complete.
gl_modem -B 1-1.2 SAT sp AT+COPS=?
```

## `network.serving_cell`

- Command: `AT+QENG="servingcell"`
- Category: serving cell
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.parsers.quectel.parse_modem`

Reports engineering data for serving cells.

Purpose: Captures LTE and NR serving-cell radio measurements.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Reports engineering data for serving cells.
# Captures LTE and NR serving-cell radio measurements.
gl_modem -B 1-1.2 AT 'AT+QENG="servingcell"'
```

## `sim.active_slot`

- Command: `AT+QUIMSLOT?`
- Category: SIM
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.providers.multisim.parse_active_slot`

Queries the active SIM slot.

Purpose: Records the original slot before multi-SIM collection.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Queries the active SIM slot.
# Records the original slot before multi-SIM collection.
gl_modem -B 1-1.2 AT 'AT+QUIMSLOT?'
```

## `sim.dual_slot_status`

- Command: `AT+QSIMCFG="dual_slot_status"`
- Category: SIM
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.providers.multisim.parse_installed_slots`

Queries dual-slot presence information.

Purpose: Enables switching only when both cards are explicitly detected.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Queries dual-slot presence information.
# Enables switching only when both cards are explicitly detected.
gl_modem -B 1-1.2 AT 'AT+QSIMCFG="dual_slot_status"'
```

## `sim.readiness`

- Command: `AT+CPIN?`
- Category: SIM
- Type: query
- Safety: read-only
- Timeout: 10 seconds
- Parser: `campnet.providers.multisim.sim_ready`

Queries active SIM readiness.

Purpose: Waits for the selected card to initialize before collection.

Expected response: Command-specific result lines followed by OK, or an exact modem error.

```bash
# Queries active SIM readiness.
# Waits for the selected card to initialize before collection.
gl_modem -B 1-1.2 AT 'AT+CPIN?'
```

## `sim.switch_slot`

- Command: `AT+QUIMSLOT=<slot>`
- Category: SIM
- Type: set/configuration
- Safety: connectivity-impacting
- Timeout: 30 seconds
- Parser: none

Selects the active SIM slot.

Purpose: Collects each installed SIM and restores the original slot.

Expected response: OK or an exact modem error; SIM initialization and registration follow asynchronously.

Side effects:

- Interrupts cellular connectivity.
- Persists the selected slot and requires restoration.

```bash
# Selects the active SIM slot.
# Collects each installed SIM and restores the original slot.
gl_modem -B 1-1.2 AT 'AT+QUIMSLOT=<slot>'
```
