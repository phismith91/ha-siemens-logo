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

.. test:: Entity base and platforms
   :id: TEST_ENTITY
   :links: SPEC_ENTITIES, REQ_ENTITY_TYPES, REQ_DEVICE_GROUPING

   ``tests/test_entity.py``, ``tests/test_binary_sensor.py``,
   ``tests/test_switch.py`` - shared ``LogoEntity`` base (normalized
   unique_id, shared ``DeviceInfo``), and that binary_sensor/switch
   platforms create the right entity type per the CSV ``type`` column.
