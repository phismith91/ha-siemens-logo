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
