# Sphinx-Needs Docs + ubCode Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `docs/superpowers/` (plain Markdown) with a Sphinx-Needs
project under `docs/`, giving the ubCode VS Code extension full editor
support and giving requirements/specs/tests explicit `req -> spec -> test`
traceability links, plus a GitHub Actions job that builds the docs and
deploys them to GitHub Pages.

**Architecture:** `docs/conf.py` configures Sphinx with the `sphinx_needs`
extension and the `furo` theme, defining three need types (`req`, `spec`,
`test`) with `REQ_`/`SPEC_`/`TEST_` ID prefixes. `docs/index.rst` holds the
root toctree pointing at four subtrees (`requirements/`, `specs/`,
`plans/`, `tests/`), built up incrementally so `sphinx-build -W` (warnings
as errors) can verify each addition before moving to the next. `ubproject.toml`
at the repo root points the ubCode extension at `docs/` as its source dir.
`docs/superpowers/` is removed once its two files are migrated.

**Tech Stack:** Sphinx, `sphinx-needs`, `furo` theme, reStructuredText,
GitHub Actions (`actions/upload-pages-artifact`, `actions/deploy-pages`).

See `docs/superpowers/specs/2026-09-29-sphinx-needs-ubcode-docs-design.md`
for the full design (read it before starting).

---

## File Structure

```
ubproject.toml                          # ubCode extension config, source dir = docs
requirements_docs.txt                   # sphinx, sphinx-needs, furo
docs/
  conf.py                               # Sphinx + sphinx-needs config
  index.rst                             # root toctree
  requirements/
    index.rst                           # req:: objects
  specs/
    index.rst
    2026-08-11-siemens-logo-integration-design.rst   # migrated design spec
  plans/
    index.rst
    2026-08-11-siemens-logo-integration.rst          # migrated plan (condensed)
  tests/
    index.rst                           # test:: objects
.github/workflows/docs.yml              # build + deploy to Pages
.claude/napkin.md                       # workflow convention note added
```

`docs/superpowers/` (the two old `.md` files) is deleted in Task 6. Nothing
outside `docs/`, the repo-root `ubproject.toml`/`requirements_docs.txt`,
`.github/workflows/docs.yml`, and `.claude/napkin.md` is touched.

**Note on the migrated plan:** the original
`docs/superpowers/plans/2026-08-11-siemens-logo-integration.md` is 2254
lines — 19 tasks, each with full TDD step-by-step code. That level of
step-by-step instructional detail was for the agent that implemented it
(now mostly done in the `feature/integration-skeleton` branch) and isn't
useful to reproduce verbatim in a docs site. Task 4 below migrates a
condensed version: goal, architecture, file structure, and the 19 task
titles with a one-line objective each. The full original text remains
available in git history (`git log --all --oneline -- docs/superpowers/plans/2026-08-11-siemens-logo-integration.md`
after Task 6 deletes it).

---

### Task 1: Scaffold — ubproject.toml, requirements_docs.txt, conf.py, empty index.rst

**Files:**
- Create: `ubproject.toml`
- Create: `requirements_docs.txt`
- Create: `docs/conf.py`
- Create: `docs/index.rst`

- [ ] **Step 1: Create `ubproject.toml`**

```toml
"$schema" = "https://ubcode.useblocks.com/ubproject.schema.json"

[project]
name = "ha-siemens-logo"

[source]
dir = "docs"
```

- [ ] **Step 2: Create `requirements_docs.txt`**

```
sphinx
sphinx-needs
furo
```

- [ ] **Step 3: Install the docs dependencies**

Run: `pip install -r requirements_docs.txt`
Expected: installs `sphinx`, `sphinx-needs`, `furo` and their dependencies
without error.

- [ ] **Step 4: Create `docs/conf.py`**

```python
project = "ha-siemens-logo"
copyright = "2026, phismith91"
author = "phismith91"

extensions = ["sphinx_needs"]

needs_types = [
    dict(directive="req", title="Requirement", prefix="REQ_", color="#BFD8D2", style="node"),
    dict(directive="spec", title="Specification", prefix="SPEC_", color="#FEDCD2", style="node"),
    dict(directive="test", title="Test", prefix="TEST_", color="#DF744A", style="node"),
]

exclude_patterns = ["_build"]

html_theme = "furo"
```

- [ ] **Step 5: Create `docs/index.rst` with an empty toctree**

```rst
ha-siemens-logo documentation
==============================

.. toctree::
   :maxdepth: 2
```

- [ ] **Step 6: Verify the build**

Run: `sphinx-build -b html docs docs/_build/html -W`
Expected: `build succeeded.` with no warnings.

- [ ] **Step 7: Commit**

```bash
git add ubproject.toml requirements_docs.txt docs/conf.py docs/index.rst
git commit -m "docs: scaffold Sphinx-Needs project for ubCode support"
```

---

### Task 2: Requirements

**Files:**
- Create: `docs/requirements/index.rst`
- Modify: `docs/index.rst`

- [ ] **Step 1: Create `docs/requirements/index.rst`**

```rst
Requirements
============

.. req:: Connection setup with dedup
   :id: REQ_CONN_SETUP

   The config flow verifies connectivity with a read probe before creating
   the config entry. The entry's unique ID is ``f"{host}:{port}"``; adding
   the same LOGO! device a second time is rejected via
   ``self._abort_if_unique_id_configured()``, not silently duplicated.

.. req:: CSV import
   :id: REQ_CSV_IMPORT

   The options flow accepts a CSV file (columns ``name,address,type``) via
   Home Assistant's native ``selector.FileSelector``. Re-importing the same
   or an updated CSV is idempotent: rows are matched to existing entities by
   normalized address, not duplicated.

.. req:: Manual entity add
   :id: REQ_MANUAL_ADD

   The options flow offers a manual entity add step (name, address, type)
   as a fallback for users without a CSV file.

.. req:: Address normalization
   :id: REQ_ADDR_NORMALIZE

   Addresses are normalized (stripped, uppercased) before use as a
   lookup/merge key, so ``v1.0`` and ``V1.0`` resolve to the same entity
   instead of creating a duplicate.

.. req:: Chunked Modbus reads
   :id: REQ_CHUNKED_READ

   The coordinator groups configured addresses into contiguous-ish ranges
   and issues one ``read_coils`` per group per poll cycle, splitting a
   group whenever its span would exceed a 1968-coil safe cap, to stay under
   Modbus's 2000-coil protocol limit for ``read_coils`` (function code 01).

.. req:: Reconnect on read
   :id: REQ_RECONNECT

   Before each poll, the coordinator checks whether the Modbus client is
   connected and reconnects if not, since ``AsyncModbusTcpClient`` does not
   reliably auto-reconnect a dropped TCP socket.

.. req:: Entity types
   :id: REQ_ENTITY_TYPES

   Digital inputs (``I1``-``I24``) become read-only ``binary_sensor``
   entities. Digital outputs (``Q1``-``Q20``) become read/write ``switch``
   entities. VM merker bits (``M1``-``M64``) become ``binary_sensor`` or
   ``switch`` depending on the CSV ``type`` column, since a merker's role
   depends on how the user's LOGO! program uses it.

.. req:: Shared device grouping
   :id: REQ_DEVICE_GROUPING

   All entities created from one config entry share one ``DeviceInfo``
   (``identifiers: {(DOMAIN, entry_id)}``), so they appear grouped under a
   single device card instead of listed loose under the integration.

.. req:: Network Input/Output direction warning
   :id: REQ_DIRECTION_WARNING

   The README documents that Modbus TCP carries no direction metadata: a
   "Network Output" block (written by the LOGO! program) must be configured
   as ``binary_sensor`` (read-only), never ``switch``, because a HA write to
   it is silently overwritten by the LOGO!'s own next program cycle. Only
   "Network Input" blocks are safe to configure as ``switch``.

.. req:: Error handling
   :id: REQ_ERROR_HANDLING

   Connection loss raises ``UpdateFailed``, entities go ``unavailable``,
   standard coordinator backoff retries. A malformed CSV row is skipped,
   logged as a warning, and surfaced as one HA Repair issue summarizing all
   skipped rows per config entry. An invalid address in the manual-add form
   produces an inline validation error in the options flow.
```

- [ ] **Step 2: Add `requirements/index` to the root toctree**

Replace `docs/index.rst` with:

```rst
ha-siemens-logo documentation
==============================

.. toctree::
   :maxdepth: 2

   requirements/index
```

- [ ] **Step 3: Verify the build**

Run: `sphinx-build -b html docs docs/_build/html -W`
Expected: `build succeeded.`, no warnings, and the 10 `REQ_*` objects appear
in `docs/_build/html/requirements/index.html`.

- [ ] **Step 4: Commit**

```bash
git add docs/requirements/index.rst docs/index.rst
git commit -m "docs: add LOGO! integration requirements as req:: objects"
```

---

### Task 3: Specs (migrate the design doc)

**Files:**
- Create: `docs/specs/index.rst`
- Create: `docs/specs/2026-08-11-siemens-logo-integration-design.rst`
- Modify: `docs/index.rst`

- [ ] **Step 1: Create `docs/specs/index.rst`**

```rst
Specs
=====

.. toctree::
   :maxdepth: 1

   2026-08-11-siemens-logo-integration-design
```

- [ ] **Step 2: Create `docs/specs/2026-08-11-siemens-logo-integration-design.rst`**

```rst
Siemens LOGO! 8 Integration Design
===================================

:Date: 2026-08-11 (revised 2026-09-22 after implementation-readiness review)
:Status: Approved

Goal
----

HACS-distributable Home Assistant custom integration for Siemens LOGO! 8
(0BA8) PLCs, with setup comfort matching the existing ``luxorliving``
integration: enter connection details, drop a config file, entities appear.
Full GitHub CI/CD with TDD, HACS validation, and a stable/pre-release
pipeline.

Non-goals (v1)
--------------

- No ``.lsc`` (LOGO!Soft Comfort project file) binary parsing. Format is
  proprietary and undocumented; no known open parser exists. Revisit as a
  later phase once a real sample file can be inspected for feasibility.
- No analog I/O (AI/AQ/AM), counters, or RTC/schedule functions. v1 covers
  digital I/O and VM merker bits only.
- No support for older LOGO! generations (0BA7 and earlier) or the
  proprietary LOGO! web-service/JSON-RPC protocol.
- No options-flow UI to change the poll interval. ``DEFAULT_SCAN_INTERVAL``
  (5s) is fixed for v1; making it user-configurable is a v2 options-flow
  step.
- No options-flow step to remove a single entity. v1 workaround: edit the
  config entry's options directly, or remove and re-add the integration.

.. spec:: Architecture
   :id: SPEC_ARCHITECTURE
   :links: REQ_CHUNKED_READ, REQ_RECONNECT

   ``custom_components/siemens_logo/``, HA domain ``siemens_logo``.
   Connectivity via ``pymodbus`` (``AsyncModbusTcpClient``) - Modbus TCP is
   LOGO! 8's open, documented interface. A single ``DataUpdateCoordinator``
   polls all configured VM addresses per cycle, fixed interval 5s in v1, no
   per-entity polling.

   **Read batching is chunked, not a single min-max span.** Modbus
   ``read_coils`` (function code 01) has a hard protocol limit of 2000
   coils per request. A naive
   ``read_coils(min(addr), max(addr)-min(addr)+1)`` breaks as soon as
   configured addresses are sparse (e.g. ``V1.0`` and ``V923.0`` together
   already span 7377 bits). The coordinator instead sorts configured
   addresses, groups them into contiguous-ish ranges (starting a new group
   whenever the gap to the next address would push the group span past the
   1968-coil safe cap), and issues one ``read_coils`` per group per poll
   cycle. For the address counts this integration targets (tens of
   entities, not thousands), this is normally one read; chunking only
   kicks in for wide or sparse address layouts.

   **Reconnect on read.** ``AsyncModbusTcpClient`` does not reliably
   auto-reconnect a dropped TCP socket. Before each poll, the coordinator
   checks ``client.connected`` and calls ``client.connect()`` again if
   not - standard coordinator backoff still applies if that reconnect
   itself fails.

.. spec:: Addressing
   :id: SPEC_ADDRESSING
   :links: REQ_ADDR_NORMALIZE, REQ_DIRECTION_WARNING

   LOGO! 8 does *not* expose local I/Q/M as Modbus coils by any fixed,
   universal address. Only signals the user has explicitly routed to VM
   memory in their own LOGO!Soft Comfort program (via "Network
   Input"/"Network Output" blocks, which have a *user-assigned* VM address
   per instance) are visible over Modbus. There is no static lookup table
   to build - any such table would be a guess presented as fact, and would
   silently write to the wrong bit on write operations.

   The CSV ``address`` column takes the **raw VM address** the user
   configured in their own program: byte.bit form for coils (``V923.0``),
   word form for future analog support (``V300``). No symbolic
   ``I1``/``Q3``/``M12`` translation. The integration's README documents
   how to find this address in LOGO!Soft Comfort (Network Input/Output
   block properties). Addresses are normalized (stripped, uppercased)
   before use as a lookup/merge key.

   **Direction mismatch is a user-configuration risk this integration
   cannot validate.** A "Network Input" block is written by the external
   Modbus client (HA) to feed a signal into the LOGO! program; a "Network
   Output" block is written by the LOGO! program itself so an external
   client can read it. Modbus TCP exposes both as plain readable/writable
   coils - the protocol carries no direction metadata. If a user configures
   a Network-Output-backed address as ``switch`` (read/write), HA's write
   will be silently overwritten by the LOGO!'s own next program cycle (the
   entity appears to "snap back"). There is no way to detect this from the
   Modbus side; the README must warn explicitly.

.. spec:: Setup flow
   :id: SPEC_SETUP_FLOW
   :links: REQ_CONN_SETUP, REQ_CSV_IMPORT, REQ_MANUAL_ADD

   1. **Config Flow:** host, port (default 502), unit/slave ID (default
      1). Connection is verified with a read probe before the entry is
      created. The entry's unique ID is ``f"{host}:{port}"``; adding the
      same LOGO! twice is rejected, not silently duplicated.
   2. **Options Flow - CSV import:** uses HA's native
      ``selector.FileSelector`` to accept a CSV with columns
      ``name,address,type`` (``type`` is ``binary_sensor`` or ``switch``).
      Re-import is idempotent - matches existing entities by address, does
      not duplicate.
   3. **Options Flow - manual entity add:** fallback for users without a
      CSV; one form per entity (name, address, type).

   CSV can be hand-written or produced from a LOGO!Soft Comfort
   symbol-table export. This is the closest available approximation to
   "drag a file in and it just works" without depending on unverified
   binary parsing.

.. spec:: Entities
   :id: SPEC_ENTITIES
   :links: REQ_ENTITY_TYPES, REQ_DEVICE_GROUPING

   - Digital inputs (``I1``-``I24``) -> ``binary_sensor``, read-only.
   - Digital outputs (``Q1``-``Q20``) -> ``switch``, read/write.
   - VM merker bits (``M1``-``M64``) -> ``binary_sensor`` (read-only) or
     ``switch`` (read/write), per the CSV ``type`` column - merkers can be
     either depending on how the user's LOGO! program uses them.
   - All entities share one ``DeviceInfo`` per config entry (``identifiers:
     {(DOMAIN, entry_id)}``), so they appear grouped under a single device
     card in HA.
   - Entity ``unique_id`` is ``f"{entry_id}_{normalized_address}"`` - not
     the raw user-typed address string.

.. spec:: Error handling
   :id: SPEC_ERROR_HANDLING
   :links: REQ_ERROR_HANDLING

   - Connection lost -> coordinator raises ``UpdateFailed``; entities go
     ``unavailable``; standard coordinator backoff retry, no custom retry
     loop.
   - Malformed CSV row -> skipped, logged as a warning, and surfaced as an
     HA Repair issue summarizing all skipped rows (not a silent failure,
     not a hard crash of the whole import).
   - Invalid address in the manual-add form -> inline validation error in
     the options flow.

Operational notes (README)
---------------------------

- LOGO! 8 supports up to 8 concurrent Modbus TCP connections (Siemens
  Industry Support forum, thread 179237). This integration holds one. Not
  a code constraint, but worth a README line since users sometimes also
  run LOGO!Soft Comfort's live monitor against the same device.
- The direction-mismatch risk (Network Input vs Network Output, see
  Addressing) is a README warning, not a code check.

Testing (TDD)
-------------

``pytest`` + ``pytest-homeassistant-custom-component``. Coverage: CSV
parser (valid rows, malformed rows, re-import/idempotency), symbolic
address -> VM-offset translator, coordinator batching (single read for a
contiguous address set, and chunking once the span exceeds the 1968-coil
cap), config flow (connection success/failure), options flow (CSV import,
manual add, validation errors). Modbus I/O is mocked in all tests - no
dependency on real hardware in CI.

``pytest_plugins = "pytest_homeassistant_custom_component"`` must live in
the project's **root-level** ``conftest.py``, not ``tests/conftest.py``.
pytest 8 deprecates/rejects ``pytest_plugins`` in a non-root conftest.

HACS / repo conventions
------------------------

Mirrors ``luxorliving`` (same author, proven pattern): ``hacs.json``,
``manifest.json`` (``requirements: ["pymodbus>=3.10.0,<4.0"]``,
``dependencies: ["file_upload"]`` for the CSV options-flow step's
``process_uploaded_file``), ``translations/{en,de}.json``, PR-only
workflow, branch protection on ``main``, required status checks
(``Pre-commit checks``, ``Run Tests``, ``validate-hacs``,
``validate-hassfest``), ``CHANGELOG.md``.

CI/CD (GitHub-hosted runners)
-------------------------------

- ``pre-commit.yml``: black, isort, flake8, bandit, prettier, trailing
  whitespace, end-of-file-fixer, check-yaml/json/toml, detect-private-key
- ``test.yml``: pytest on every push/PR
- ``validate-hacs.yml``, ``validate-hassfest.yml``: official HACS/hassfest
  GitHub Actions
- ``release.yml``: triggered on tag push. ``vX.Y.Z`` -> stable GitHub
  Release, ``vX.Y.Z-rc.N`` -> GitHub pre-release. Both attach a
  ``siemens_logo.zip`` of ``custom_components/siemens_logo`` (HACS
  installs from release assets).

Development process
--------------------

Full superpowers workflow for every feature: brainstorming -> spec doc ->
writing-plans -> TDD -> code review -> finishing-a-development-branch.
Every change on its own branch, PR into ``main``, never pushed directly.
```

- [ ] **Step 3: Add `specs/index` to the root toctree**

Replace `docs/index.rst` with:

```rst
ha-siemens-logo documentation
==============================

.. toctree::
   :maxdepth: 2

   requirements/index
   specs/index
```

- [ ] **Step 4: Verify the build**

Run: `sphinx-build -b html docs docs/_build/html -W`
Expected: `build succeeded.`, no warnings, no "undefined label" or
"unknown need id" errors for the `REQ_*` links used in `:links:`.

- [ ] **Step 5: Commit**

```bash
git add docs/specs/index.rst docs/specs/2026-08-11-siemens-logo-integration-design.rst docs/index.rst
git commit -m "docs: migrate design spec to RST with spec:: objects"
```

---

### Task 4: Plans (condensed migration)

**Files:**
- Create: `docs/plans/index.rst`
- Create: `docs/plans/2026-08-11-siemens-logo-integration.rst`
- Modify: `docs/index.rst`

- [ ] **Step 1: Create `docs/plans/index.rst`**

```rst
Plans
=====

.. toctree::
   :maxdepth: 1

   2026-08-11-siemens-logo-integration
```

- [ ] **Step 2: Create `docs/plans/2026-08-11-siemens-logo-integration.rst`**

```rst
Siemens LOGO! 8 Integration Implementation Plan
=================================================

.. note::

   This is a condensed reference. The original plan
   (``docs/superpowers/plans/2026-08-11-siemens-logo-integration.md``,
   removed when this Sphinx-Needs docs tree was introduced) had full
   TDD step-by-step detail - failing test code, exact commands, expected
   output - for all 19 tasks below. That detail is preserved in git
   history: ``git log --all --oneline -- docs/superpowers/plans/2026-08-11-siemens-logo-integration.md``.

Goal
----

Ship a HACS-installable Home Assistant custom integration that talks to a
Siemens LOGO! 8 over Modbus TCP, with CSV-import setup comfort and a full
GitHub CI/CD + stable/pre-release pipeline. See :doc:`../specs/2026-08-11-siemens-logo-integration-design`
for the full design.

Architecture
------------

``custom_components/siemens_logo/`` - a ``DataUpdateCoordinator`` chunks
Modbus coil reads for all configured VM addresses into batches that
respect the 2000-coil Modbus protocol limit, and reconnects before polling
if the TCP session dropped; ``binary_sensor`` and ``switch`` platforms
share one ``LogoEntity`` base (normalized unique_id, shared ``DeviceInfo``
so all entities group under one device card); config flow handles
connection setup (with host:port dedup) and options flow handles CSV
import / manual entity add.

Tech Stack
----------

Python 3.13, Home Assistant custom component APIs, pymodbus 3.x
(``AsyncModbusTcpClient``), pytest + pytest-homeassistant-custom-component,
GitHub Actions.

File Structure
--------------

.. code-block:: text

   conftest.py                            # root-level: registers HA test plugin
   custom_components/siemens_logo/
     __init__.py         # entry setup/unload, coordinator + client wiring
     const.py             # DOMAIN, CONF_* keys, defaults
     address.py            # VM address string <-> flat Modbus coil address, normalization
     csv_import.py          # CSV parsing into entity configs
     modbus_client.py        # thin async pymodbus wrapper (connect/read/write/connected)
     coordinator.py           # DataUpdateCoordinator subclass, chunked reads, reconnect
     entity.py                 # LogoEntity base: unique_id, DeviceInfo, shared by platforms
     config_flow.py            # ConfigFlow (connection, unique_id dedup) + OptionsFlow
     binary_sensor.py           # read-only entities
     switch.py                   # read/write entities
     manifest.json
     strings.json
     translations/en.json
     translations/de.json
   tests/
     conftest.py
     test_address.py
     test_csv_import.py
     test_modbus_client.py
     test_coordinator.py
     test_config_flow.py
     test_options_flow.py
     test_entity.py
     test_binary_sensor.py
     test_switch.py
     test_init.py
   hacs.json
   README.md
   CHANGELOG.md
   LICENSE
   .gitignore
   requirements_test.txt
   pyproject.toml
   .flake8
   .pre-commit-config.yaml
   .github/workflows/pre-commit.yml
   .github/workflows/test.yml
   .github/workflows/validate-hacs.yml
   .github/workflows/validate-hassfest.yml
   .github/workflows/release.yml

Each module has one job: ``address.py`` never touches Modbus,
``modbus_client.py`` never touches HA, ``coordinator.py`` never touches
CSV, ``entity.py`` never touches Modbus directly (goes through the
coordinator).

Tasks
-----

#. Repo skeleton and packaging metadata
#. VM address parser + normalization (TDD)
#. CSV import parser (TDD)
#. Modbus client wrapper (TDD, mocked pymodbus)
#. Data update coordinator - chunked reads + reconnect (TDD)
#. Config flow - connection step + unique_id dedup (TDD)
#. Options flow - CSV import step (TDD)
#. Options flow - manual add step (TDD)
#. Shared entity base - unique_id + device grouping (TDD)
#. Integration setup/unload wiring (TDD)
#. binary_sensor platform (TDD)
#. switch platform (TDD)
#. Full test suite + coverage check
#. pre-commit configuration
#. CI workflows - pre-commit and tests
#. CI workflows - HACS and hassfest validation
#. Release pipeline (stable + pre-release)
#. README, CHANGELOG, and merge
#. Branch protection and first pre-release
```

- [ ] **Step 3: Add `plans/index` to the root toctree**

Replace `docs/index.rst` with:

```rst
ha-siemens-logo documentation
==============================

.. toctree::
   :maxdepth: 2

   requirements/index
   specs/index
   plans/index
```

- [ ] **Step 4: Verify the build**

Run: `sphinx-build -b html docs docs/_build/html -W`
Expected: `build succeeded.`, no warnings (the `:doc:` cross-reference to
the spec resolves cleanly since Task 3 already created that file).

- [ ] **Step 5: Commit**

```bash
git add docs/plans/index.rst docs/plans/2026-08-11-siemens-logo-integration.rst docs/index.rst
git commit -m "docs: migrate implementation plan (condensed) to RST"
```

---

### Task 5: Tests

**Files:**
- Create: `docs/tests/index.rst`
- Modify: `docs/index.rst`

- [ ] **Step 1: Create `docs/tests/index.rst`**

```rst
Tests
=====

.. test:: Address parser and normalization
   :id: TEST_ADDRESS
   :links: SPEC_ADDRESSING, REQ_ADDR_NORMALIZE

   ``tests/test_address.py`` - VM address string <-> flat Modbus coil
   address conversion, and that ``v1.0``/``V1.0`` normalize to the same
   key.

.. test:: CSV import
   :id: TEST_CSV_IMPORT
   :links: SPEC_SETUP_FLOW, REQ_CSV_IMPORT, REQ_ERROR_HANDLING

   ``tests/test_csv_import.py`` - valid rows, malformed rows (skipped +
   repair issue), and idempotent re-import (no duplicate entities, type
   preserved for untouched entities).

.. test:: Modbus client wrapper
   :id: TEST_MODBUS_CLIENT
   :links: SPEC_ARCHITECTURE, REQ_RECONNECT

   ``tests/test_modbus_client.py`` - connect/read/write/connected against
   a mocked ``AsyncModbusTcpClient``, no real hardware.

.. test:: Coordinator batching and reconnect
   :id: TEST_COORDINATOR
   :links: SPEC_ARCHITECTURE, REQ_CHUNKED_READ, REQ_RECONNECT

   ``tests/test_coordinator.py`` - single read for a contiguous address
   set, chunking into multiple reads once the span exceeds the 1968-coil
   cap, and reconnect-before-poll behavior including the case where
   reconnect itself fails (wrapped in ``UpdateFailed``).

.. test:: Config flow
   :id: TEST_CONFIG_FLOW
   :links: SPEC_SETUP_FLOW, REQ_CONN_SETUP

   ``tests/test_config_flow.py`` - connection success/failure, and that
   host:port dedup short-circuits before the connection attempt.

.. test:: Options flow
   :id: TEST_OPTIONS_FLOW
   :links: SPEC_SETUP_FLOW, REQ_CSV_IMPORT, REQ_MANUAL_ADD, REQ_ERROR_HANDLING

   ``tests/test_options_flow.py`` - CSV import step, manual entity add
   step, and inline validation errors for invalid manual addresses.
```

- [ ] **Step 2: Add `tests/index` to the root toctree**

Replace `docs/index.rst` with:

```rst
ha-siemens-logo documentation
==============================

.. toctree::
   :maxdepth: 2

   requirements/index
   specs/index
   plans/index
   tests/index
```

- [ ] **Step 3: Verify the build**

Run: `sphinx-build -b html docs docs/_build/html -W`
Expected: `build succeeded.`, no warnings. Open
`docs/_build/html/requirements/index.html` and confirm each `REQ_*` object
now shows a "linked by" back-reference from the matching `SPEC_*`/`TEST_*`
objects (sphinx-needs generates this automatically).

- [ ] **Step 4: Commit**

```bash
git add docs/tests/index.rst docs/index.rst
git commit -m "docs: add test:: objects linking pytest modules to specs/requirements"
```

---

### Task 6: Remove the migrated docs/superpowers/ files

**Files:**
- Delete: `docs/superpowers/specs/2026-08-11-siemens-logo-integration-design.md`
- Delete: `docs/superpowers/plans/2026-08-11-siemens-logo-integration.md`

These two are the files migrated in Tasks 3 and 4 — now superseded by
`docs/specs/2026-08-11-siemens-logo-integration-design.rst` and
`docs/plans/2026-08-11-siemens-logo-integration.rst`. Their content stays
in this branch's git history.

This deliberately does **not** touch
`docs/superpowers/specs/2026-09-29-sphinx-needs-ubcode-docs-design.md` or
`docs/superpowers/plans/2026-09-29-sphinx-needs-ubcode-docs.md` — this
feature's own spec and the plan file you're executing right now. Deleting
the plan you're mid-execution of would break whichever agent/skill is
reading Tasks 7-9 from it. Those two are removed as the very last step of
Task 9, once nothing needs to read them anymore.

- [ ] **Step 1: Remove the two migrated files**

```bash
git rm docs/superpowers/specs/2026-08-11-siemens-logo-integration-design.md \
       docs/superpowers/plans/2026-08-11-siemens-logo-integration.md
```

- [ ] **Step 2: Verify the build is unaffected**

Run: `sphinx-build -b html docs docs/_build/html -W`
Expected: `build succeeded.`, no warnings — `docs/superpowers/` was never
part of the Sphinx source tree, so removing files from it doesn't change
the build.

- [ ] **Step 3: Commit**

```bash
git commit -m "docs: remove migrated docs/superpowers/ files, superseded by Sphinx-Needs docs"
```

---

### Task 7: CI — build and deploy docs to GitHub Pages

**Files:**
- Create: `.github/workflows/docs.yml`

- [ ] **Step 1: Create the workflow**

```yaml
name: Docs

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install -r requirements_docs.txt
      - run: sphinx-build -b html docs docs/_build/html -W
      - uses: actions/upload-pages-artifact@v3
        if: github.ref == 'refs/heads/main'
        with:
          path: docs/_build/html

  deploy:
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/docs.yml'))"`
Expected: no output, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/docs.yml
git commit -m "ci: build and deploy docs to GitHub Pages"
```

---

### Task 8: Napkin — record the workflow convention change

**Files:**
- Modify: `.claude/napkin.md`

- [ ] **Step 1: Add a new entry under "User Directives"**

In `.claude/napkin.md`, after the existing item 3 ("Mirror luxorliving repo
conventions") under `## User Directives`, add:

```markdown
4. **[2026-09-29] Sphinx-Needs docs replace docs/superpowers/**
   Do instead: specs go to `docs/specs/YYYY-MM-DD-<topic>-design.rst`
   (`spec::` objects linking `req::` IDs), plans go to
   `docs/plans/YYYY-MM-DD-<topic>.rst` (plain RST, condensed for large
   plans — see the note at the top of
   `docs/plans/2026-08-11-siemens-logo-integration.rst` for the pattern).
   Requirements live in `docs/requirements/index.rst` as `req::` objects.
   Tests get `test::` objects in `docs/tests/index.rst` linking to the
   `spec::`/`req::` IDs they verify. ubCode (VS Code extension) config:
   `ubproject.toml` at repo root, `[source] dir = "docs"`. Build check:
   `sphinx-build -b html docs docs/_build/html -W`.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/napkin.md
git commit -m "napkin: record RST/Sphinx-Needs convention for specs and plans"
```

---

### Task 9: Final verification and self-cleanup

**Files:**
- Delete: `docs/superpowers/specs/2026-09-29-sphinx-needs-ubcode-docs-design.md`
- Delete: `docs/superpowers/plans/2026-09-29-sphinx-needs-ubcode-docs.md`

- [ ] **Step 1: Clean build from scratch**

```bash
rm -rf docs/_build
sphinx-build -b html docs docs/_build/html -W
```

Expected: `build succeeded.`, no warnings.

- [ ] **Step 2: Confirm nothing else is left uncommitted**

```bash
git status --short
```

Expected: only the two files from this task's own `git rm` (added in Step
3 below) show up, nothing else.

- [ ] **Step 3: Remove this feature's own spec and plan files**

All other tasks are done and committed at this point, so nothing needs to
read Tasks 7-9 from the plan file anymore.

```bash
git rm docs/superpowers/specs/2026-09-29-sphinx-needs-ubcode-docs-design.md \
       docs/superpowers/plans/2026-09-29-sphinx-needs-ubcode-docs.md
```

This also removes the now-empty `docs/superpowers/` directory (git doesn't
track empty directories).

- [ ] **Step 4: Confirm `docs/superpowers/` is fully gone and the new tree is in place**

```bash
git ls-files docs | sort
```

Expected: only files under `docs/conf.py`, `docs/index.rst`,
`docs/requirements/`, `docs/specs/`, `docs/plans/`, `docs/tests/` — no
`docs/superpowers/*`.

- [ ] **Step 5: Commit**

```bash
git commit -m "docs: remove this feature's own spec/plan, migration complete"
```
