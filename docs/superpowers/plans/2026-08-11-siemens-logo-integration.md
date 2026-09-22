# Siemens LOGO! 8 HA Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a HACS-installable Home Assistant custom integration that talks
to a Siemens LOGO! 8 over Modbus TCP, with CSV-import setup comfort and a full
GitHub CI/CD + stable/pre-release pipeline.

**Architecture:** `custom_components/siemens_logo/` — a `DataUpdateCoordinator`
chunks Modbus coil reads for all configured VM addresses into batches that
respect the 2000-coil Modbus protocol limit, and reconnects before polling if
the TCP session dropped; `binary_sensor` and `switch` platforms share one
`LogoEntity` base (normalized unique_id, shared `DeviceInfo` so all entities
group under one device card); config flow handles connection setup (with
host:port dedup) and options flow handles CSV import / manual entity add.
See `docs/superpowers/specs/2026-08-11-siemens-logo-integration-design.md`
for the full design (read it before starting — this plan implements it,
including the 2026-09-22 revision: chunked batching, reconnect-on-read,
address normalization, device grouping, `file_upload` manifest dependency,
root-level `conftest.py` placement, and the Network Input/Output direction
warning).

**Tech Stack:** Python 3.13, Home Assistant custom component APIs, pymodbus
3.x (`AsyncModbusTcpClient`), pytest + pytest-homeassistant-custom-component,
GitHub Actions.

---

## File Structure

```
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
```

Each module has one job: `address.py` never touches Modbus, `modbus_client.py`
never touches HA, `coordinator.py` never touches CSV, `entity.py` never
touches Modbus directly (goes through the coordinator). This keeps every file
independently testable without a running Home Assistant instance except
where the HA test harness is explicitly needed (config/options flow,
platforms).

---

### Task 1: Repo skeleton and packaging metadata

**Files:**
- Create: `custom_components/siemens_logo/__init__.py` (empty stub for now)
- Create: `custom_components/siemens_logo/const.py`
- Create: `custom_components/siemens_logo/manifest.json`
- Create: `hacs.json`
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `requirements_test.txt`
- Create: `pyproject.toml`
- Create: `.flake8`

- [ ] **Step 1: Create the package stub and const module**

`custom_components/siemens_logo/__init__.py`:
```python
"""The Siemens LOGO! integration."""
```

`custom_components/siemens_logo/const.py`:
```python
"""Constants for the Siemens LOGO! integration."""

DOMAIN = "siemens_logo"

CONF_UNIT_ID = "unit_id"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ENTITIES = "entities"

DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1
DEFAULT_SCAN_INTERVAL = 5

ENTITY_TYPES = ["binary_sensor", "switch"]
```

- [ ] **Step 2: Write manifest.json and hacs.json**

`custom_components/siemens_logo/manifest.json`:
```json
{
  "domain": "siemens_logo",
  "name": "Siemens LOGO!",
  "codeowners": ["@phismith91"],
  "config_flow": true,
  "dependencies": ["file_upload"],
  "documentation": "https://github.com/phismith91/ha-siemens-logo",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/phismith91/ha-siemens-logo/issues",
  "requirements": ["pymodbus>=3.6.0,<4.0"],
  "version": "0.1.0"
}
```

`"dependencies": ["file_upload"]` is required because the options flow's CSV
import step uses `homeassistant.components.file_upload.process_uploaded_file`
(Task 7) — without declaring the dependency, HA does not guarantee
`file_upload` is set up before this integration, and the import will fail.
Same pattern as HA core's `mqtt` and `zha` manifests.

`hacs.json`:
```json
{
  "name": "Siemens LOGO!",
  "render_readme": true
}
```

- [ ] **Step 3: Write dev tooling config**

`.gitignore`:
```
__pycache__/
*.pyc
.venv/
venv/
.pytest_cache/
.coverage
htmlcov/
*.egg-info/
.mypy_cache/
```

`requirements_test.txt`:
```
pytest
pytest-asyncio
pytest-cov
pytest-homeassistant-custom-component
pymodbus>=3.6.0,<4.0
```

`pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ["py313"]

[tool.isort]
profile = "black"

[tool.bandit]
exclude_dirs = ["tests"]
```

`.flake8`:
```
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .venv,venv,.git,__pycache__
```

`LICENSE`: MIT license text, copyright holder "Philipp Schmidt", year 2026.

- [ ] **Step 4: Commit**

```bash
git checkout -b feature/integration-skeleton
git add custom_components hacs.json .gitignore requirements_test.txt pyproject.toml .flake8 LICENSE
git commit -m "chore: repo skeleton, manifest, dev tooling config"
```

---

### Task 2: VM address parser + normalization (TDD)

**Files:**
- Create: `custom_components/siemens_logo/address.py`
- Test: `tests/test_address.py`
- Create: `tests/__init__.py` (empty, makes it a package)

- [ ] **Step 1: Write the failing tests**

`tests/__init__.py`: empty file.

`tests/test_address.py`:
```python
"""Tests for VM address parsing and normalization."""
import pytest

from custom_components.siemens_logo.address import normalize_vm_address, parse_vm_address


def test_parses_valid_byte_bit_address():
    assert parse_vm_address("V923.0") == 923 * 8
    assert parse_vm_address("V923.7") == 923 * 8 + 7


def test_strips_whitespace_and_is_case_insensitive():
    assert parse_vm_address(" v10.3 ") == 10 * 8 + 3


def test_rejects_missing_v_prefix():
    with pytest.raises(ValueError, match="Invalid VM address"):
        parse_vm_address("923.0")


def test_rejects_bit_out_of_range():
    with pytest.raises(ValueError, match="Invalid VM address"):
        parse_vm_address("V923.8")


def test_rejects_garbage():
    with pytest.raises(ValueError, match="Invalid VM address"):
        parse_vm_address("not-an-address")


def test_normalize_strips_and_uppercases():
    assert normalize_vm_address(" v10.3 ") == "V10.3"


def test_normalize_is_idempotent():
    assert normalize_vm_address("V10.3") == normalize_vm_address(normalize_vm_address("V10.3"))


def test_normalize_rejects_garbage():
    with pytest.raises(ValueError, match="Invalid VM address"):
        normalize_vm_address("not-an-address")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_address.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'custom_components.siemens_logo.address'`

- [ ] **Step 3: Implement the parser**

`custom_components/siemens_logo/address.py`:
```python
"""VM address parsing for Siemens LOGO! Modbus addressing.

LOGO! 8 does not expose local I/Q/M via any fixed Modbus address -- only
VM addresses the user has explicitly wired to a Network Input/Output block
in their own LOGO!Soft Comfort program are reachable over Modbus. See
docs/superpowers/specs/2026-08-11-siemens-logo-integration-design.md.
"""
from __future__ import annotations

import re

_VM_BIT_RE = re.compile(r"^V(\d+)\.([0-7])$")


def _match(address: str) -> re.Match[str]:
    match = _VM_BIT_RE.match(address.strip().upper())
    if not match:
        raise ValueError(
            f"Invalid VM address: {address!r} (expected format 'V<byte>.<bit>', "
            "e.g. 'V923.0')"
        )
    return match


def parse_vm_address(address: str) -> int:
    """Parse a LOGO! VM bit address like 'V923.0' into a flat Modbus coil address.

    Raises ValueError if the address is not in valid byte.bit form.
    """
    match = _match(address)
    byte, bit = int(match.group(1)), int(match.group(2))
    return byte * 8 + bit


def normalize_vm_address(address: str) -> str:
    """Return the canonical string form of a VM address (stripped, uppercased).

    Used as the merge/lookup key for CSV re-import and as the unique_id
    suffix, so 'v1.0' and 'V1.0' resolve to the same entity instead of
    creating a duplicate. Raises ValueError if the address is invalid.
    """
    return _match(address).group(0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_address.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add custom_components/siemens_logo/address.py tests/test_address.py tests/__init__.py
git commit -m "feat: VM address parser and normalization"
```

---

### Task 3: CSV import parser (TDD)

**Files:**
- Create: `custom_components/siemens_logo/csv_import.py`
- Test: `tests/test_csv_import.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_csv_import.py`:
```python
"""Tests for CSV entity-config import."""
from custom_components.siemens_logo.csv_import import parse_csv


def test_parses_valid_rows():
    content = "name,address,type\nFront Door,V923.0,binary_sensor\nGarage Light,V924.1,switch\n"
    result = parse_csv(content)
    assert result.errors == []
    assert len(result.entities) == 2
    assert result.entities[0].name == "Front Door"
    assert result.entities[0].address == "V923.0"
    assert result.entities[0].flat_address == 923 * 8
    assert result.entities[0].entity_type == "binary_sensor"


def test_normalizes_address_case_and_whitespace():
    content = "name,address,type\nFront Door, v923.0 ,binary_sensor\n"
    result = parse_csv(content)
    assert result.entities[0].address == "V923.0"


def test_rejects_missing_header_columns():
    result = parse_csv("name,address\nFront Door,V923.0\n")
    assert result.entities == []
    assert "must contain columns" in result.errors[0]


def test_skips_row_with_invalid_address_and_keeps_others():
    content = "name,address,type\nBad,not-an-address,switch\nGood,V1.0,switch\n"
    result = parse_csv(content)
    assert len(result.entities) == 1
    assert result.entities[0].name == "Good"
    assert "Row 2" in result.errors[0]


def test_skips_row_with_invalid_type():
    content = "name,address,type\nBad,V1.0,sensor\n"
    result = parse_csv(content)
    assert result.entities == []
    assert "invalid type" in result.errors[0]


def test_skips_row_with_empty_name():
    content = "name,address,type\n,V1.0,switch\n"
    result = parse_csv(content)
    assert result.entities == []
    assert "missing name" in result.errors[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_csv_import.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the parser**

`custom_components/siemens_logo/csv_import.py`:
```python
"""CSV import for Siemens LOGO! entity configuration."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

from .address import normalize_vm_address, parse_vm_address

VALID_TYPES = {"binary_sensor", "switch"}
REQUIRED_COLUMNS = {"name", "address", "type"}


@dataclass(frozen=True)
class EntityConfig:
    name: str
    address: str  # normalized (stripped, uppercased) VM address string
    flat_address: int
    entity_type: str


@dataclass
class CsvImportResult:
    entities: list[EntityConfig] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def parse_csv(content: str) -> CsvImportResult:
    """Parse CSV text (name,address,type) into entity configs.

    Malformed rows are skipped and recorded in `errors`, valid rows are
    still returned -- a single bad row must not block the whole import.
    Addresses are normalized so re-importing the same VM address in a
    different case/whitespace form updates the same entity.
    """
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
        return CsvImportResult(
            errors=[f"CSV header must contain columns: {', '.join(sorted(REQUIRED_COLUMNS))}"]
        )

    result = CsvImportResult()
    for line_no, row in enumerate(reader, start=2):
        name = (row.get("name") or "").strip()
        address = (row.get("address") or "").strip()
        entity_type = (row.get("type") or "").strip()

        if not name:
            result.errors.append(f"Row {line_no}: missing name")
            continue
        if entity_type not in VALID_TYPES:
            result.errors.append(
                f"Row {line_no}: invalid type {entity_type!r} "
                f"(must be one of {sorted(VALID_TYPES)})"
            )
            continue
        try:
            normalized = normalize_vm_address(address)
            flat_address = parse_vm_address(normalized)
        except ValueError as err:
            result.errors.append(f"Row {line_no}: {err}")
            continue

        result.entities.append(
            EntityConfig(
                name=name, address=normalized, flat_address=flat_address, entity_type=entity_type
            )
        )

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_csv_import.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add custom_components/siemens_logo/csv_import.py tests/test_csv_import.py
git commit -m "feat: CSV entity-config import"
```

---

### Task 4: Modbus client wrapper (TDD, mocked pymodbus)

**Files:**
- Create: `custom_components/siemens_logo/modbus_client.py`
- Test: `tests/test_modbus_client.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_modbus_client.py`:
```python
"""Tests for the LOGO! Modbus client wrapper."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.siemens_logo.modbus_client import LogoModbusClient


@pytest.mark.asyncio
async def test_connect_delegates_to_pymodbus():
    with patch(
        "custom_components.siemens_logo.modbus_client.AsyncModbusTcpClient"
    ) as mock_cls:
        mock_cls.return_value.connect = AsyncMock(return_value=True)
        client = LogoModbusClient("10.0.0.5", 502, 1)
        assert await client.connect() is True


def test_connected_property_delegates_to_pymodbus():
    with patch(
        "custom_components.siemens_logo.modbus_client.AsyncModbusTcpClient"
    ) as mock_cls:
        mock_cls.return_value.connected = True
        client = LogoModbusClient("10.0.0.5", 502, 1)
        assert client.connected is True


@pytest.mark.asyncio
async def test_read_coils_returns_bit_list():
    with patch(
        "custom_components.siemens_logo.modbus_client.AsyncModbusTcpClient"
    ) as mock_cls:
        response = MagicMock(bits=[True, False, True, False], **{"isError.return_value": False})
        mock_cls.return_value.read_coils = AsyncMock(return_value=response)
        client = LogoModbusClient("10.0.0.5", 502, 1)
        bits = await client.read_coils(100, 3)
        assert bits == [True, False, True]
        mock_cls.return_value.read_coils.assert_awaited_once_with(100, count=3, slave=1)


@pytest.mark.asyncio
async def test_read_coils_raises_on_error_response():
    with patch(
        "custom_components.siemens_logo.modbus_client.AsyncModbusTcpClient"
    ) as mock_cls:
        response = MagicMock(**{"isError.return_value": True})
        mock_cls.return_value.read_coils = AsyncMock(return_value=response)
        client = LogoModbusClient("10.0.0.5", 502, 1)
        with pytest.raises(ConnectionError, match="read_coils failed"):
            await client.read_coils(100, 3)


@pytest.mark.asyncio
async def test_write_coil_delegates_to_pymodbus():
    with patch(
        "custom_components.siemens_logo.modbus_client.AsyncModbusTcpClient"
    ) as mock_cls:
        response = MagicMock(**{"isError.return_value": False})
        mock_cls.return_value.write_coil = AsyncMock(return_value=response)
        client = LogoModbusClient("10.0.0.5", 502, 1)
        await client.write_coil(100, True)
        mock_cls.return_value.write_coil.assert_awaited_once_with(100, True, slave=1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modbus_client.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the wrapper**

`custom_components/siemens_logo/modbus_client.py`:
```python
"""Thin async wrapper around pymodbus for a LOGO! 8 Modbus TCP server."""
from __future__ import annotations

from pymodbus.client import AsyncModbusTcpClient


class LogoModbusClient:
    """Owns one Modbus TCP connection to a single LOGO! 8 device."""

    def __init__(self, host: str, port: int, unit_id: int) -> None:
        self._client = AsyncModbusTcpClient(host, port=port)
        self._unit_id = unit_id

    @property
    def connected(self) -> bool:
        return self._client.connected

    async def connect(self) -> bool:
        return await self._client.connect()

    def close(self) -> None:
        self._client.close()

    async def read_coils(self, address: int, count: int) -> list[bool]:
        result = await self._client.read_coils(address, count=count, slave=self._unit_id)
        if result.isError():
            raise ConnectionError(f"Modbus read_coils failed at address {address}: {result}")
        return list(result.bits[:count])

    async def write_coil(self, address: int, value: bool) -> None:
        result = await self._client.write_coil(address, value, slave=self._unit_id)
        if result.isError():
            raise ConnectionError(f"Modbus write_coil failed at address {address}: {result}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modbus_client.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add custom_components/siemens_logo/modbus_client.py tests/test_modbus_client.py
git commit -m "feat: Modbus TCP client wrapper"
```

---

### Task 5: Data update coordinator — chunked reads + reconnect (TDD)

**Files:**
- Create: `conftest.py` (project root)
- Create: `custom_components/siemens_logo/coordinator.py`
- Test: `tests/test_coordinator.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write the root-level conftest.py**

`conftest.py` (repo root, next to `pyproject.toml` — **not** under `tests/`):
```python
"""Root pytest config. Registers the HA test plugin globally.

Must live at the project root: pytest 8 deprecates/rejects
`pytest_plugins` declared in a non-root conftest.py.
"""
pytest_plugins = "pytest_homeassistant_custom_component"
```

`tests/conftest.py`:
```python
"""Shared fixtures for Siemens LOGO! integration tests."""
import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield
```

- [ ] **Step 2: Write the failing tests**

`tests/test_coordinator.py`:
```python
"""Tests for the LOGO! data update coordinator."""
from unittest.mock import AsyncMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.siemens_logo.coordinator import LogoDataCoordinator


@pytest.mark.asyncio
async def test_batches_reads_into_a_single_call(hass):
    client = AsyncMock()
    client.connected = True
    client.read_coils.return_value = [True, False, False, True]
    # addresses 100 and 103 -> single read_coils(100, count=4)
    coordinator = LogoDataCoordinator(hass, client, addresses=[100, 103], scan_interval=5)

    data = await coordinator._async_update_data()

    client.read_coils.assert_awaited_once_with(100, 4)
    assert data == {100: True, 103: True}


@pytest.mark.asyncio
async def test_chunks_reads_when_span_exceeds_cap(hass):
    client = AsyncMock()
    client.connected = True
    client.read_coils.side_effect = [[True], [False]]
    # addresses 0 and 2000 span 2001 coils, past the 1968 cap -> two reads
    coordinator = LogoDataCoordinator(hass, client, addresses=[0, 2000], scan_interval=5)

    data = await coordinator._async_update_data()

    assert client.read_coils.await_count == 2
    client.read_coils.assert_any_await(0, 1)
    client.read_coils.assert_any_await(2000, 1)
    assert data == {0: True, 2000: False}


@pytest.mark.asyncio
async def test_reconnects_before_read_if_disconnected(hass):
    client = AsyncMock()
    client.connected = False
    client.read_coils.return_value = [True]
    coordinator = LogoDataCoordinator(hass, client, addresses=[100], scan_interval=5)

    await coordinator._async_update_data()

    client.connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_empty_address_list_skips_modbus_call(hass):
    client = AsyncMock()
    coordinator = LogoDataCoordinator(hass, client, addresses=[], scan_interval=5)

    data = await coordinator._async_update_data()

    client.read_coils.assert_not_awaited()
    assert data == {}


@pytest.mark.asyncio
async def test_read_error_raises_update_failed(hass):
    client = AsyncMock()
    client.connected = True
    client.read_coils.side_effect = ConnectionError("boom")
    coordinator = LogoDataCoordinator(hass, client, addresses=[100], scan_interval=5)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_async_write_coil_writes_and_refreshes(hass):
    client = AsyncMock()
    client.connected = True
    client.read_coils.return_value = [True]
    coordinator = LogoDataCoordinator(hass, client, addresses=[100], scan_interval=5)

    await coordinator.async_write_coil(100, True)

    client.write_coil.assert_awaited_once_with(100, True)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_coordinator.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 4: Implement the coordinator**

`custom_components/siemens_logo/coordinator.py`:
```python
"""Data update coordinator for the Siemens LOGO! integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .modbus_client import LogoModbusClient

_LOGGER = logging.getLogger(__name__)

# Modbus read_coils (function code 01) hard-limits a single request to 2000
# coils. Stay comfortably under that so one oversized group never has to be
# split again mid-flight.
MAX_COILS_PER_READ = 1968


def _group_addresses(addresses: list[int]) -> list[tuple[int, int]]:
    """Group sorted addresses into (start, count) ranges.

    Each range spans at most MAX_COILS_PER_READ coils. Addresses close
    together end up in one read; addresses far apart split into separate
    reads instead of one huge span covering mostly unused bits.
    """
    sorted_addrs = sorted(set(addresses))
    groups: list[tuple[int, int]] = []
    group_start = sorted_addrs[0]
    group_end = sorted_addrs[0]
    for addr in sorted_addrs[1:]:
        if addr - group_start + 1 > MAX_COILS_PER_READ:
            groups.append((group_start, group_end - group_start + 1))
            group_start = addr
        group_end = addr
    groups.append((group_start, group_end - group_start + 1))
    return groups


class LogoDataCoordinator(DataUpdateCoordinator[dict[int, bool]]):
    """Polls all configured VM coil addresses, chunked under the Modbus limit."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: LogoModbusClient,
        addresses: list[int],
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=scan_interval)
        )
        self._client = client
        self._addresses = addresses

    async def _async_update_data(self) -> dict[int, bool]:
        if not self._addresses:
            return {}
        if not self._client.connected:
            await self._client.connect()
        data: dict[int, bool] = {}
        try:
            for start, count in _group_addresses(self._addresses):
                bits = await self._client.read_coils(start, count)
                for addr in self._addresses:
                    if start <= addr < start + count:
                        data[addr] = bits[addr - start]
        except Exception as err:
            raise UpdateFailed(f"Error reading LOGO! Modbus data: {err}") from err
        return data

    async def async_write_coil(self, address: int, value: bool) -> None:
        await self._client.write_coil(address, value)
        await self.async_request_refresh()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_coordinator.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add conftest.py custom_components/siemens_logo/coordinator.py tests/test_coordinator.py tests/conftest.py
git commit -m "feat: chunked, reconnecting Modbus data update coordinator"
```

---

### Task 6: Config flow — connection step + unique_id dedup (TDD)

**Files:**
- Create: `custom_components/siemens_logo/config_flow.py`
- Create: `custom_components/siemens_logo/strings.json`
- Create: `custom_components/siemens_logo/translations/en.json`
- Test: `tests/test_config_flow.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_config_flow.py`:
```python
"""Tests for the Siemens LOGO! config flow."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.siemens_logo.const import DOMAIN


@pytest.mark.asyncio
async def test_successful_connection_creates_entry(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM

    with patch(
        "custom_components.siemens_logo.config_flow.LogoModbusClient"
    ) as mock_cls:
        mock_cls.return_value.connect = AsyncMock(return_value=True)
        mock_cls.return_value.close = lambda: None
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "10.0.0.5", "port": 502, "unit_id": 1},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["host"] == "10.0.0.5"


@pytest.mark.asyncio
async def test_failed_connection_shows_error(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.siemens_logo.config_flow.LogoModbusClient"
    ) as mock_cls:
        mock_cls.return_value.connect = AsyncMock(return_value=False)
        mock_cls.return_value.close = lambda: None
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "10.0.0.5", "port": 502, "unit_id": 1},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
async def test_duplicate_host_port_aborts(hass):
    with patch(
        "custom_components.siemens_logo.config_flow.LogoModbusClient"
    ) as mock_cls:
        mock_cls.return_value.connect = AsyncMock(return_value=True)
        mock_cls.return_value.close = lambda: None

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "10.0.0.5", "port": 502, "unit_id": 1}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "10.0.0.5", "port": 502, "unit_id": 1}
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config_flow.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the connection step of the config flow**

`custom_components/siemens_logo/config_flow.py`:
```python
"""Config and options flow for the Siemens LOGO! integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_UNIT_ID, DEFAULT_PORT, DEFAULT_UNIT_ID, DOMAIN
from .modbus_client import LogoModbusClient


class LogoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle initial connection setup."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()

            client = LogoModbusClient(
                user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_UNIT_ID]
            )
            try:
                connected = await client.connect()
            finally:
                client.close()

            if not connected:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=user_input[CONF_HOST], data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "LogoOptionsFlow":
        return LogoOptionsFlow(config_entry)


class LogoOptionsFlow(config_entries.OptionsFlow):
    """Placeholder -- entity setup steps added in Task 7/8."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return self.async_create_entry(title="", data=dict(self._config_entry.options))
```

`custom_components/siemens_logo/strings.json`:
```json
{
  "config": {
    "step": {
      "user": {
        "data": {
          "host": "Host",
          "port": "Port",
          "unit_id": "Unit ID"
        }
      }
    },
    "error": {
      "cannot_connect": "Cannot connect to the LOGO! at this address."
    },
    "abort": {
      "already_configured": "This LOGO! (host:port) is already configured."
    }
  }
}
```

`custom_components/siemens_logo/translations/en.json`: identical content to `strings.json` (HA convention -- copy the file).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config_flow.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
mkdir -p custom_components/siemens_logo/translations
git add custom_components/siemens_logo/config_flow.py custom_components/siemens_logo/strings.json custom_components/siemens_logo/translations/en.json tests/test_config_flow.py
git commit -m "feat: config flow connection step with host:port dedup"
```

---

### Task 7: Options flow — CSV import step (TDD)

**Files:**
- Modify: `custom_components/siemens_logo/config_flow.py`
- Modify: `custom_components/siemens_logo/strings.json`, `translations/en.json`
- Test: `tests/test_options_flow.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_options_flow.py`:
```python
"""Tests for the Siemens LOGO! options flow."""
from unittest.mock import patch

import pytest
from homeassistant.data_entry_flow import FlowResultType

from custom_components.siemens_logo.const import CONF_ENTITIES, DOMAIN


async def _create_entry(hass):
    from homeassistant.config_entries import ConfigEntry

    entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="10.0.0.5",
        data={"host": "10.0.0.5", "port": 502, "unit_id": 1},
        source="user",
        options={},
        unique_id="10.0.0.5:502",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.mark.asyncio
async def test_csv_import_creates_entities(hass, tmp_path):
    entry = await _create_entry(hass)
    csv_path = tmp_path / "entities.csv"
    csv_path.write_text("name,address,type\nFront Door,V923.0,binary_sensor\n")

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "import_csv"}
    )

    with patch(
        "custom_components.siemens_logo.config_flow.process_uploaded_file"
    ) as mock_process:
        mock_process.return_value.__enter__.return_value = csv_path
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"csv_file": "fake-file-id"}
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    entities = result["data"][CONF_ENTITIES]
    assert len(entities) == 1
    assert entities[0]["name"] == "Front Door"
    assert entities[0]["address"] == "V923.0"


@pytest.mark.asyncio
async def test_csv_reimport_is_idempotent_on_normalized_address(hass, tmp_path):
    entry = await _create_entry(hass)
    entry.options = {
        CONF_ENTITIES: [{"name": "Old Name", "address": "V923.0", "type": "binary_sensor"}]
    }
    csv_path = tmp_path / "entities.csv"
    # different case/whitespace than the stored address -- must still match
    csv_path.write_text("name,address,type\nNew Name, v923.0 ,binary_sensor\n")

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "import_csv"}
    )
    with patch(
        "custom_components.siemens_logo.config_flow.process_uploaded_file"
    ) as mock_process:
        mock_process.return_value.__enter__.return_value = csv_path
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"csv_file": "fake-file-id"}
        )

    entities = result["data"][CONF_ENTITIES]
    assert len(entities) == 1
    assert entities[0]["name"] == "New Name"
    assert entities[0]["address"] == "V923.0"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_options_flow.py -v`
Expected: FAIL — `async_step_init` doesn't support `next_step_id` menu routing yet.

- [ ] **Step 3: Implement the CSV import step**

Replace the `LogoOptionsFlow` class in `custom_components/siemens_logo/config_flow.py`:
```python
from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.helpers import selector
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue

from .address import normalize_vm_address
from .const import CONF_ENTITIES
from .csv_import import parse_csv


class LogoOptionsFlow(config_entries.OptionsFlow):
    """Manage entity setup: CSV import or manual add."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return self.async_show_menu(
            step_id="init", menu_options=["import_csv", "add_entity"]
        )

    async def async_step_import_csv(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            with process_uploaded_file(self.hass, user_input["csv_file"]) as file_path:
                content = file_path.read_text(encoding="utf-8")
            result = parse_csv(content)

            if result.errors:
                async_create_issue(
                    self.hass,
                    DOMAIN,
                    "csv_import_errors",
                    is_fixable=False,
                    severity=IssueSeverity.WARNING,
                    translation_key="csv_import_errors",
                    translation_placeholders={"errors": "; ".join(result.errors)},
                )

            existing = {
                normalize_vm_address(e["address"]): e
                for e in self._config_entry.options.get(CONF_ENTITIES, [])
            }
            for cfg in result.entities:
                existing[cfg.address] = {
                    "name": cfg.name,
                    "address": cfg.address,
                    "type": cfg.entity_type,
                }
            options = dict(self._config_entry.options)
            options[CONF_ENTITIES] = list(existing.values())
            return self.async_create_entry(title="", data=options)

        schema = vol.Schema(
            {vol.Required("csv_file"): selector.FileSelector(selector.FileSelectorConfig(accept=".csv"))}
        )
        return self.async_show_form(step_id="import_csv", data_schema=schema, errors=errors)
```

Update `custom_components/siemens_logo/strings.json` (add under a top-level
`"issues"` key, and an `"options"` step for `import_csv`):
```json
{
  "config": {
    "step": {
      "user": {
        "data": { "host": "Host", "port": "Port", "unit_id": "Unit ID" }
      }
    },
    "error": { "cannot_connect": "Cannot connect to the LOGO! at this address." },
    "abort": { "already_configured": "This LOGO! (host:port) is already configured." }
  },
  "options": {
    "step": {
      "init": {
        "menu_options": { "import_csv": "Import CSV file", "add_entity": "Add entity manually" }
      },
      "import_csv": {
        "data": { "csv_file": "CSV file (name,address,type)" }
      }
    }
  },
  "issues": {
    "csv_import_errors": {
      "title": "Some CSV rows were skipped",
      "description": "{errors}"
    }
  }
}
```
Copy the same content into `translations/en.json`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_options_flow.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add custom_components/siemens_logo/config_flow.py custom_components/siemens_logo/strings.json custom_components/siemens_logo/translations/en.json tests/test_options_flow.py
git commit -m "feat: options flow CSV import step with normalized re-import"
```

---

### Task 8: Options flow — manual add step (TDD)

**Files:**
- Modify: `custom_components/siemens_logo/config_flow.py`
- Modify: `strings.json`, `translations/en.json`
- Modify: `tests/test_options_flow.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_options_flow.py`:
```python
@pytest.mark.asyncio
async def test_manual_add_creates_entity(hass):
    entry = await _create_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "add_entity"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"name": "Garage Light", "address": "V924.1", "type": "switch"},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    entities = result["data"][CONF_ENTITIES]
    assert entities[0]["name"] == "Garage Light"
    assert entities[0]["address"] == "V924.1"


@pytest.mark.asyncio
async def test_manual_add_normalizes_address(hass):
    entry = await _create_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "add_entity"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"name": "Garage Light", "address": " v924.1 ", "type": "switch"},
    )

    entities = result["data"][CONF_ENTITIES]
    assert entities[0]["address"] == "V924.1"


@pytest.mark.asyncio
async def test_manual_add_rejects_invalid_address(hass):
    entry = await _create_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "add_entity"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"name": "Bad", "address": "not-an-address", "type": "switch"},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"address": "invalid_address"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_options_flow.py -v`
Expected: FAIL — no `async_step_add_entity` handler.

- [ ] **Step 3: Implement the manual-add step**

Add to `LogoOptionsFlow` in `config_flow.py` (and import `ENTITY_TYPES` from
`.const`, alongside the existing `normalize_vm_address` import from
`.address`):
```python
    async def async_step_add_entity(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                normalized = normalize_vm_address(user_input["address"])
            except ValueError:
                errors["address"] = "invalid_address"
            else:
                existing = {
                    normalize_vm_address(e["address"]): e
                    for e in self._config_entry.options.get(CONF_ENTITIES, [])
                }
                existing[normalized] = {
                    "name": user_input["name"],
                    "address": normalized,
                    "type": user_input["type"],
                }
                options = dict(self._config_entry.options)
                options[CONF_ENTITIES] = list(existing.values())
                return self.async_create_entry(title="", data=options)

        schema = vol.Schema(
            {
                vol.Required("name"): str,
                vol.Required("address"): str,
                vol.Required("type", default="binary_sensor"): vol.In(ENTITY_TYPES),
            }
        )
        return self.async_show_form(step_id="add_entity", data_schema=schema, errors=errors)
```

Add `from .const import CONF_ENTITIES, ENTITY_TYPES` (merge with the existing
`.const` import in that file). Extend `strings.json`/`translations/en.json`'s
`options.step` with:
```json
      "add_entity": {
        "data": { "name": "Name", "address": "VM address (e.g. V923.0)", "type": "Entity type" }
      },
```
and an `options.error` block:
```json
    "error": { "invalid_address": "Not a valid VM address (expected 'V<byte>.<bit>')." }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_options_flow.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add custom_components/siemens_logo/config_flow.py custom_components/siemens_logo/strings.json custom_components/siemens_logo/translations/en.json tests/test_options_flow.py
git commit -m "feat: options flow manual entity add step with address normalization"
```

---

### Task 9: Shared entity base — unique_id + device grouping (TDD)

**Files:**
- Create: `custom_components/siemens_logo/entity.py`
- Test: `tests/test_entity.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_entity.py`:
```python
"""Tests for the shared LOGO! entity base."""
from unittest.mock import MagicMock

from custom_components.siemens_logo.entity import LogoEntity


def test_unique_id_uses_normalized_address():
    coordinator = MagicMock()
    entity = LogoEntity(coordinator, "entry1", "LOGO! 10.0.0.5", "Door", " v1.0 ")
    assert entity.unique_id == "entry1_V1.0"


def test_flat_address_parsed_from_normalized_form():
    coordinator = MagicMock()
    entity = LogoEntity(coordinator, "entry1", "LOGO! 10.0.0.5", "Door", "V1.0")
    assert entity._flat_address == 8


def test_device_info_groups_entities_under_one_device():
    coordinator = MagicMock()
    entity_a = LogoEntity(coordinator, "entry1", "LOGO! 10.0.0.5", "Door", "V1.0")
    entity_b = LogoEntity(coordinator, "entry1", "LOGO! 10.0.0.5", "Window", "V2.0")
    assert entity_a.device_info == entity_b.device_info
    assert entity_a.device_info["name"] == "LOGO! 10.0.0.5"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_entity.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the base class**

`custom_components/siemens_logo/entity.py`:
```python
"""Shared entity base for Siemens LOGO! platforms.

Every entity is one VM coil address. All entities from the same config
entry share one DeviceInfo, so they group under a single device card in
HA instead of listing loose under the integration.
"""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .address import normalize_vm_address, parse_vm_address
from .const import DOMAIN


class LogoEntity(CoordinatorEntity):
    """Base for all Siemens LOGO! VM-bit entities."""

    def __init__(
        self, coordinator, entry_id: str, device_name: str, name: str, address: str
    ) -> None:
        super().__init__(coordinator)
        normalized = normalize_vm_address(address)
        self._flat_address = parse_vm_address(normalized)
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{normalized}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=device_name,
            manufacturer="Siemens",
            model="LOGO! 8",
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_entity.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add custom_components/siemens_logo/entity.py tests/test_entity.py
git commit -m "feat: shared entity base with normalized unique_id and device grouping"
```

---

### Task 10: Integration setup/unload wiring (TDD)

**Files:**
- Modify: `custom_components/siemens_logo/__init__.py`
- Test: `tests/test_init.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_init.py`:
```python
"""Tests for integration setup/unload."""
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.siemens_logo.const import CONF_ENTITIES, DOMAIN


@pytest.mark.asyncio
async def test_setup_entry_connects_and_forwards_platforms(hass):
    from homeassistant.config_entries import ConfigEntry

    entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="10.0.0.5",
        data={"host": "10.0.0.5", "port": 502, "unit_id": 1},
        source="user",
        options={CONF_ENTITIES: [{"name": "Door", "address": "V1.0", "type": "binary_sensor"}]},
        unique_id="10.0.0.5:502",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.siemens_logo.LogoModbusClient"
    ) as mock_cls:
        mock_cls.return_value.connect = AsyncMock(return_value=True)
        mock_cls.return_value.connected = True
        mock_cls.return_value.close = lambda: None
        mock_cls.return_value.read_coils = AsyncMock(return_value=[True])

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.entry_id in hass.data[DOMAIN]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_init.py -v`
Expected: FAIL — `async_setup_entry` not defined.

- [ ] **Step 3: Implement `__init__.py`**

`custom_components/siemens_logo/__init__.py`:
```python
"""The Siemens LOGO! integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .address import parse_vm_address
from .const import (
    CONF_ENTITIES,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import LogoDataCoordinator
from .modbus_client import LogoModbusClient

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = LogoModbusClient(
        entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_UNIT_ID]
    )
    if not await client.connect():
        raise ConfigEntryNotReady(f"Cannot connect to LOGO! at {entry.data[CONF_HOST]}")

    entity_configs = entry.options.get(CONF_ENTITIES, [])
    addresses = [parse_vm_address(cfg["address"]) for cfg in entity_configs]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = LogoDataCoordinator(hass, client, addresses, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "device_name": f"LOGO! {entry.title}",
    }

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        data["client"].close()
    return unload_ok
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_init.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add custom_components/siemens_logo/__init__.py tests/test_init.py
git commit -m "feat: integration setup/unload wiring"
```

---

### Task 11: binary_sensor platform (TDD)

**Files:**
- Create: `custom_components/siemens_logo/binary_sensor.py`
- Test: `tests/test_binary_sensor.py`

- [ ] **Step 1: Write the failing test**

`tests/test_binary_sensor.py`:
```python
"""Tests for the LOGO! binary_sensor platform."""
from unittest.mock import MagicMock

from custom_components.siemens_logo.binary_sensor import LogoBinarySensor


def test_is_on_reads_from_coordinator_data():
    coordinator = MagicMock()
    coordinator.data = {8: True, 16: False}
    sensor_on = LogoBinarySensor(coordinator, "entry1", "LOGO! 10.0.0.5", "Door", "V1.0")
    sensor_off = LogoBinarySensor(coordinator, "entry1", "LOGO! 10.0.0.5", "Window", "V2.0")

    assert sensor_on.is_on is True
    assert sensor_off.is_on is False
    assert sensor_on.unique_id == "entry1_V1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_binary_sensor.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the platform**

`custom_components/siemens_logo/binary_sensor.py`:
```python
"""Binary sensor platform for Siemens LOGO!."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENTITIES, DOMAIN
from .entity import LogoEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = stored["coordinator"]
    device_name = stored["device_name"]
    async_add_entities(
        LogoBinarySensor(coordinator, entry.entry_id, device_name, cfg["name"], cfg["address"])
        for cfg in entry.options.get(CONF_ENTITIES, [])
        if cfg["type"] == "binary_sensor"
    )


class LogoBinarySensor(LogoEntity, BinarySensorEntity):
    """A read-only LOGO! VM bit."""

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(self._flat_address)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_binary_sensor.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add custom_components/siemens_logo/binary_sensor.py tests/test_binary_sensor.py
git commit -m "feat: binary_sensor platform"
```

---

### Task 12: switch platform (TDD)

**Files:**
- Create: `custom_components/siemens_logo/switch.py`
- Test: `tests/test_switch.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_switch.py`:
```python
"""Tests for the LOGO! switch platform."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.siemens_logo.switch import LogoSwitch


def test_is_on_reads_from_coordinator_data():
    coordinator = MagicMock()
    coordinator.data = {8: True}
    switch = LogoSwitch(coordinator, "entry1", "LOGO! 10.0.0.5", "Garage Light", "V1.0")
    assert switch.is_on is True


@pytest.mark.asyncio
async def test_turn_on_writes_coil_true():
    coordinator = MagicMock()
    coordinator.async_write_coil = AsyncMock()
    switch = LogoSwitch(coordinator, "entry1", "LOGO! 10.0.0.5", "Garage Light", "V1.0")

    await switch.async_turn_on()

    coordinator.async_write_coil.assert_awaited_once_with(8, True)


@pytest.mark.asyncio
async def test_turn_off_writes_coil_false():
    coordinator = MagicMock()
    coordinator.async_write_coil = AsyncMock()
    switch = LogoSwitch(coordinator, "entry1", "LOGO! 10.0.0.5", "Garage Light", "V1.0")

    await switch.async_turn_off()

    coordinator.async_write_coil.assert_awaited_once_with(8, False)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_switch.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the platform**

`custom_components/siemens_logo/switch.py`:
```python
"""Switch platform for Siemens LOGO!."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENTITIES, DOMAIN
from .entity import LogoEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = stored["coordinator"]
    device_name = stored["device_name"]
    async_add_entities(
        LogoSwitch(coordinator, entry.entry_id, device_name, cfg["name"], cfg["address"])
        for cfg in entry.options.get(CONF_ENTITIES, [])
        if cfg["type"] == "switch"
    )


class LogoSwitch(LogoEntity, SwitchEntity):
    """A read/write LOGO! VM bit."""

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(self._flat_address)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_coil(self._flat_address, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_coil(self._flat_address, False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_switch.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add custom_components/siemens_logo/switch.py tests/test_switch.py
git commit -m "feat: switch platform"
```

---

### Task 13: Full test suite + coverage check

**Files:** none created — verification task.

- [ ] **Step 1: Run the entire suite**

Run: `pytest --cov=custom_components/siemens_logo --cov-report=term-missing -v`
Expected: all tests pass (Tasks 2–12 combined: ~40 tests).

- [ ] **Step 2: Fix any integration-level failures**

If tests fail here that passed individually, it's almost always an
`options={}` vs `options=None` mismatch, a missing `unique_id` on a
hand-built `ConfigEntry` in a test, or an `entry.add_to_hass` ordering
issue — check that every test builds its `ConfigEntry` the same way as
`_create_entry` in `tests/test_options_flow.py`. Fix inline, re-run.

- [ ] **Step 3: Commit if any fixes were made**

```bash
git add -A
git commit -m "fix: cross-test integration fixes"
```

(Skip this commit if Step 1 passed clean.)

---

### Task 14: pre-commit configuration

**Files:**
- Create: `.pre-commit-config.yaml`

- [ ] **Step 1: Write the config**

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 7.1.1
    hooks:
      - id: flake8
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.10
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: debug-statements
      - id: detect-private-key
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        types_or: [yaml, json, markdown]
```

- [ ] **Step 2: Install and run locally**

Run: `pip install pre-commit && pre-commit install && pre-commit run --all-files`
Expected: hooks run; fix any black/isort/flake8 findings they report, then
re-run until clean.

- [ ] **Step 3: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "chore: pre-commit configuration"
```

(Include any auto-formatting changes pre-commit made in this same commit.)

---

### Task 15: CI workflows — pre-commit and tests

**Files:**
- Create: `.github/workflows/pre-commit.yml`
- Create: `.github/workflows/test.yml`

- [ ] **Step 1: Write the workflows**

`.github/workflows/pre-commit.yml`:
```yaml
name: Pre-commit checks

on:
  push:
    branches: [main]
  pull_request:

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - uses: pre-commit/action@v3.0.1
```

`.github/workflows/test.yml`:
```yaml
name: Run Tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install -r requirements_test.txt
      - run: pytest --cov=custom_components/siemens_logo --cov-report=term-missing
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/pre-commit.yml .github/workflows/test.yml
git commit -m "ci: pre-commit and test workflows"
```

---

### Task 16: CI workflows — HACS and hassfest validation

**Files:**
- Create: `.github/workflows/validate-hacs.yml`
- Create: `.github/workflows/validate-hassfest.yml`

- [ ] **Step 1: Write the workflows**

`.github/workflows/validate-hacs.yml`:
```yaml
name: Validate HACS

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: "0 0 * * *"

jobs:
  validate-hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hacs/action@main
        with:
          category: integration
```

`.github/workflows/validate-hassfest.yml`:
```yaml
name: Validate hassfest

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: "0 0 * * *"

jobs:
  hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/validate-hacs.yml .github/workflows/validate-hassfest.yml
git commit -m "ci: HACS and hassfest validation workflows"
```

---

### Task 17: Release pipeline (stable + pre-release)

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Write the workflow**

`.github/workflows/release.yml`:
```yaml
name: Release

on:
  push:
    tags:
      - "v*.*.*"

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set manifest version from tag
        run: |
          VERSION="${GITHUB_REF#refs/tags/v}"
          jq --arg version "$VERSION" '.version = $version' \
            custom_components/siemens_logo/manifest.json > /tmp/manifest.json
          mv /tmp/manifest.json custom_components/siemens_logo/manifest.json

      - name: Build release zip
        run: |
          cd custom_components/siemens_logo
          zip -r ../../siemens_logo.zip .

      - name: Determine prerelease flag
        id: prerelease
        run: |
          if [[ "${GITHUB_REF#refs/tags/}" == *-rc.* ]]; then
            echo "flag=true" >> "$GITHUB_OUTPUT"
          else
            echo "flag=false" >> "$GITHUB_OUTPUT"
          fi

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: siemens_logo.zip
          prerelease: ${{ steps.prerelease.outputs.flag }}
          generate_release_notes: true
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "ci: release pipeline for stable and pre-release tags"
```

---

### Task 18: README, CHANGELOG, and merge

**Files:**
- Create: `README.md`
- Create: `CHANGELOG.md`

- [ ] **Step 1: Write README.md**

`README.md`:
```markdown
# Siemens LOGO! 8 for Home Assistant

Talks to a Siemens LOGO! 8 (0BA8) over Modbus TCP. Digital I/O and VM
merker bits only -- no analog, no counters, no `.lsc` project-file import
(see [the design spec](docs/superpowers/specs/2026-08-11-siemens-logo-integration-design.md)
for why).

## Install (HACS custom repository)

1. HACS -> Integrations -> ... -> Custom repositories
2. Add `https://github.com/phismith91/ha-siemens-logo`, category "Integration"
3. Install "Siemens LOGO!", restart Home Assistant

## Setup

1. Settings -> Devices & Services -> Add Integration -> "Siemens LOGO!"
2. Enter host, port (default 502), unit ID (default 1). Adding the same
   host:port twice is rejected -- the entry already exists.
3. Open the integration's Options and either:
   - **Import CSV file**: drop a CSV with columns `name,address,type`
   - **Add entity manually**: one form per entity
4. All entities appear grouped under one device card for this LOGO!.

## CSV format

| name         | address  | type          |
|--------------|----------|---------------|
| Front Door   | V923.0   | binary_sensor |
| Garage Light | V924.1   | switch        |

`address` is the raw VM bit address (`V<byte>.<bit>`), **not** `I1`/`Q3`/`M12`
-- LOGO! 8 has no fixed mapping from local I/Q/M to Modbus. Find the VM
address in LOGO!Soft Comfort on the properties of the Network Input/Output
block you wired to that signal in your own program.

Re-importing a CSV updates entities by matching `address` (case- and
whitespace-normalized) -- it won't duplicate existing ones.

### `switch` vs `binary_sensor` -- pick the right one

A **Network Input** block is written by Home Assistant to feed a signal
*into* your LOGO! program -- set its VM address to `switch`. A **Network
Output** block is written by the LOGO! program itself so Home Assistant
can read it -- set its VM address to `binary_sensor`.

Modbus itself carries no direction information, so this integration
**cannot detect a mismatch**. If you configure a Network Output address as
`switch`, Home Assistant's write will be silently overwritten by the
LOGO!'s own next program cycle -- the entity will appear to "snap back" to
its previous state. If that happens, double-check the block type in
LOGO!Soft Comfort and fix the `type` column.

## Operational notes

- LOGO! 8 supports up to 8 concurrent Modbus TCP connections. This
  integration holds one. If you also have LOGO!Soft Comfort's live
  monitor open against the same device, both can normally coexist, but
  keep the total client count in mind.
- The poll interval is fixed at 5 seconds in this version; it is not yet
  configurable from the UI.

## Full design

See [docs/superpowers/specs/2026-08-11-siemens-logo-integration-design.md](docs/superpowers/specs/2026-08-11-siemens-logo-integration-design.md).
```

- [ ] **Step 2: Write CHANGELOG.md**

```markdown
# Changelog

## [Unreleased]

## [0.1.0] - TBD
### Added
- Initial release: Modbus TCP connection with host:port dedup, chunked
  and reconnecting coordinator polling, CSV/manual entity setup with
  normalized addressing, binary_sensor and switch platforms grouped
  under one device per LOGO! 8.
```

- [ ] **Step 3: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: README and CHANGELOG"
```

- [ ] **Step 4: Push branch and open PR**

```bash
GIT_SSH_COMMAND='ssh -F /dev/null' git push -u origin feature/integration-skeleton
gh pr create --title "Siemens LOGO! 8 integration: v0.1.0 core" \
  --body "Implements the design in docs/superpowers/specs/2026-08-11-siemens-logo-integration-design.md: chunked/reconnecting Modbus TCP coordinator, host:port dedup, CSV/manual entity setup with normalized addressing, device-grouped binary_sensor + switch platforms, full CI/CD (pre-commit, tests, HACS/hassfest validation, release pipeline)."
```

- [ ] **Step 5: Verify CI is green, then merge**

Wait for all four checks (Pre-commit checks, Run Tests, Validate HACS,
Validate hassfest) to pass on the PR, then:
```bash
gh pr merge --squash --delete-branch
```

---

### Task 19: Branch protection and first pre-release

**Files:** none — repo administration + tag.

- [ ] **Step 1: Enable branch protection on `main`**

```bash
gh api -X PUT repos/phismith91/ha-siemens-logo/branches/main/protection \
  -f required_status_checks='{"strict":true,"contexts":["Pre-commit checks","Run Tests","validate-hacs","validate-hassfest"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews=null \
  -f restrictions=null
```

- [ ] **Step 2: Tag and publish the first pre-release**

```bash
git checkout main
GIT_SSH_COMMAND='ssh -F /dev/null' git pull
git tag v0.1.0-rc.1
GIT_SSH_COMMAND='ssh -F /dev/null' git push origin v0.1.0-rc.1
```

`release.yml` fires automatically and publishes a GitHub pre-release with
`siemens_logo.zip` attached — HACS custom-repo installs pick this up.

- [ ] **Step 3: Confirm the release**

```bash
gh release view v0.1.0-rc.1
```
Expected: release exists, marked "Pre-release", `siemens_logo.zip` attached.

---

## Explicitly deferred (see spec's Non-goals)

- `.lsc` binary project-file import — needs a real sample file for a
  feasibility spike before any design/plan work starts.
- Analog I/O (AI/AQ/AM), counters, RTC/schedule functions.
- Older LOGO! generations (0BA7 and earlier), LOGO! web-service protocol.
- Options-flow UI to change the poll interval (v2).
- Options-flow step to remove a single entity (v2).
- Submission to the official `home-assistant/brands` repo (for a proper
  HACS icon) and to the default HACS integration list — both are follow-up
  PRs once v0.1.0 has real-world validation, not part of this plan.
