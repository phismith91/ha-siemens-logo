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
