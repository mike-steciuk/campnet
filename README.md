# CampNet

CampNet creates reproducible cellular-connectivity field surveys for campers,
RVers, and remote workers.

> CampNet measures what the modem observes—not just what the carrier
> advertises.

The project is in its bootstrap phase. The current executable establishes the
provider architecture, canonical Survey model, and JSON persistence layer.
Hardware collection providers will be added against captured modem fixtures.

## Quick start

```powershell
python -m campnet collect --campground "Petoskey State Park" --site "212"
python -m campnet show surveys\<survey-file>.json
```

Replay the checked-in modem fixture through the AT provider:

```powershell
python -m campnet collect `
  --at-fixture tests\fixtures\quectel_basic.json `
  --profile continuous `
  --output surveys\fixture-survey.json
```

Collect live read-only modem observations through a configured router:

```powershell
python -m campnet collect --ssh-host 192.168.8.1
```

The live transport uses OpenSSH batch mode and GL.iNet's `gl_modem` helper.
It does not accept or persist passwords, passphrases, or private keys.
Collection prints a human-readable report and saves the complete versioned
survey, including raw responses, beneath the ignored `surveys/` directory.
The default `one-off` profile includes slow `COPS` and `QSCAN` discovery plus
temporary GNSS enablement. CampNet restores GNSS to its previous disabled
state afterward. Use `--profile continuous` for fast radio sampling; that
profile omits slow discovery and never enables GNSS. Use `--no-gps` to omit
GNSS from an individual one-off survey.

Use `--output` to choose a specific JSON path. No provider currently changes
modem state; GNSS enablement will remain opt-in when its provider is added.

See [CampNet_Development_Spec.md](CampNet_Development_Spec.md) for the living
product and engineering specification.

Router authentication is intentionally handled outside CampNet. See
[docs/development.md](docs/development.md) for the key-based OpenWrt SSH setup.

## Sensitive survey data

Live surveys, captures, and raw-response directories are ignored by Git.
Never force-add field data. Only deliberately redacted modem responses belong
in `tests/fixtures/`; use `tests/fixtures/private/` for local, unredacted test
captures that must remain untracked.
