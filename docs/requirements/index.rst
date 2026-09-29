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
