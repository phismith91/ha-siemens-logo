# Design: Home Assistant Integration for Siemens LOGO! 8

**Date:** 2026-08-11
**Status:** Approved
**Repo:** https://github.com/phismith91/ha-siemens-logo

## Goal

HACS-distributable Home Assistant custom integration for Siemens LOGO! 8
(0BA8) PLCs, with setup comfort matching the existing `luxorliving`
integration: enter connection details, drop a config file, entities appear.
Full GitHub CI/CD with TDD, HACS validation, and a stable/pre-release
pipeline.

## Non-goals (v1)

- No `.lsc` (LOGO!Soft Comfort project file) binary parsing. Format is
  proprietary and undocumented; no known open parser exists. Revisit as a
  later phase once a real sample file can be inspected for feasibility.
- No analog I/O (AI/AQ/AM), counters, or RTC/schedule functions. v1 covers
  digital I/O and VM merker bits only.
- No support for older LOGO! generations (0BA7 and earlier) or the
  proprietary LOGO! web-service/JSON-RPC protocol.

## Architecture

- `custom_components/siemens_logo/`, HA domain `siemens_logo`.
- Connectivity via `pymodbus` (`AsyncModbusTcpClient`) — Modbus TCP is
  LOGO! 8's open, documented interface.
- A single `DataUpdateCoordinator` polls all configured VM addresses in one
  batched Modbus read per cycle (default interval: 5s, configurable in
  options). No per-entity polling.

## Addressing

**Corrected 2026-08-11 after research (see napkin.md):** LOGO! 8 does
*not* expose local I/Q/M as Modbus coils by any fixed, universal address.
Only signals the user has explicitly routed to VM memory in their own
LOGO!Soft Comfort program (via "Network Input"/"Network Output" blocks,
which have a *user-assigned* VM address per instance) are visible over
Modbus. There is no static lookup table to build — any such table would
be a guess presented as fact, and would silently write to the wrong bit
on write operations.

The CSV `address` column therefore takes the **raw VM address** the user
configured in their own program: byte.bit form for coils (`V923.0`),
word form for future analog support (`V300`). No symbolic `I1`/`Q3`/`M12`
translation. The integration's README documents how to find this address
in LOGO!Soft Comfort (Network Input/Output block properties).

## Setup flow

1. **Config Flow:** host, port (default 502), unit/slave ID (default 1).
   Connection is verified with a read probe before the entry is created.
2. **Options Flow — CSV import:** uses HA's native `selector.FileSelector`
   (the same "drop a file into HA" UX pattern other core integrations use
   for file-based config) to accept a CSV with columns
   `name,address,type` (`type` is `binary_sensor` or `switch`). Re-import
   is idempotent — matches existing entities by address, does not
   duplicate.
3. **Options Flow — manual entity add:** fallback for users without a CSV;
   one form per entity (name, address, direction).

CSV can be hand-written or produced from a LOGO!Soft Comfort symbol-table
export. This is the closest available approximation to "drag a file in and
it just works" without depending on unverified binary parsing.

## Entities (v1)

- Digital inputs (`I1`–`I24`) → `binary_sensor`, read-only.
- Digital outputs (`Q1`–`Q20`) → `switch`, read/write.
- VM merker bits (`M1`–`M64`) → `binary_sensor` (read-only) or `switch`
  (read/write), per the CSV `type` column — merkers can be either
  depending on how the user's LOGO! program uses them.

## Error handling

- Connection lost → coordinator raises `UpdateFailed`; entities go
  `unavailable`; standard coordinator backoff retry, no custom retry loop.
- Malformed CSV row → skipped, logged as a warning, and surfaced as an HA
  Repair issue summarizing all skipped rows (not a silent failure, not a
  hard crash of the whole import).
- Invalid address in the manual-add form → inline validation error in the
  options flow.

## Testing (TDD)

`pytest` + `pytest-homeassistant-custom-component`. Coverage:

- CSV parser (valid rows, malformed rows, re-import/idempotency)
- Symbolic-address → VM-offset translator
- Coordinator batching (single Modbus read covering all configured
  addresses)
- Config flow (connection success/failure)
- Options flow (CSV import, manual add, validation errors)

Modbus I/O is mocked in all tests — no dependency on real hardware in CI.

## HACS / repo conventions

Mirrors `luxorliving` (same author, proven pattern):

- `hacs.json`, `manifest.json` (`requirements: ["pymodbus"]`),
  `translations/{en,de}.json`
- PR-only workflow, branch protection on `main`, required status checks:
  `Pre-commit checks`, `Run Tests`, `validate-hacs`, `validate-hassfest`
- `CHANGELOG.md`

## CI/CD (GitHub-hosted runners)

- `pre-commit.yml`: black, isort, flake8, bandit, prettier, trailing
  whitespace, end-of-file-fixer, check-yaml/json/toml, detect-private-key
- `test.yml`: pytest on every push/PR
- `validate-hacs.yml`, `validate-hassfest.yml`: official HACS/hassfest
  GitHub Actions
- `release.yml`: triggered on tag push.
  - `vX.Y.Z` → stable GitHub Release
  - `vX.Y.Z-rc.N` → GitHub pre-release
  - Both attach a `siemens_logo.zip` of `custom_components/siemens_logo`
    (HACS installs from release assets)

## Development process

Full superpowers workflow for every feature: brainstorming → spec doc →
writing-plans → TDD (`superpowers:test-driven-development`) →
`superpowers:requesting-code-review` → `superpowers:finishing-a-development-branch`.
Every change on its own branch, PR into `main`, never pushed directly.
