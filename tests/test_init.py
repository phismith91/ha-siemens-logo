from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.siemens_logo import _parse_points
from custom_components.siemens_logo.const import DOMAIN
from custom_components.siemens_logo.coordinator import SiemensLogoCoordinator
from custom_components.siemens_logo.models import LogoPoint

_VALID_RAW = [
    {"key": "q1", "name": "Q1", "platform": "switch", "kind": "coil", "address": 8192},
    {"key": "i1", "name": "I1", "platform": "binary_sensor", "kind": "discrete", "address": 1},
    {"key": "ai1", "name": "AI1", "platform": "sensor", "kind": "holding", "address": 0},
]


# ---------------------------------------------------------------------------
# _parse_points – pure unit tests (no HA needed)
# ---------------------------------------------------------------------------


def test_parse_valid_points() -> None:
    points = _parse_points(_VALID_RAW)
    assert len(points) == 3
    assert all(isinstance(p, LogoPoint) for p in points)


def test_parse_empty_list() -> None:
    assert _parse_points([]) == []


def test_parse_missing_required_field_skipped() -> None:
    # "address" is missing
    raw = [{"key": "x", "name": "X", "platform": "sensor", "kind": "holding"}]
    assert _parse_points(raw) == []


def test_parse_invalid_platform_skipped() -> None:
    raw = [{"key": "x", "name": "X", "platform": "light", "kind": "coil", "address": 0}]
    assert _parse_points(raw) == []


def test_parse_invalid_kind_skipped() -> None:
    raw = [{"key": "x", "name": "X", "platform": "sensor", "kind": "unknown", "address": 0}]
    assert _parse_points(raw) == []


def test_parse_optional_field_defaults() -> None:
    raw = [{"key": "x", "name": "X", "platform": "sensor", "kind": "holding", "address": 5}]
    points = _parse_points(raw)
    assert len(points) == 1
    assert points[0].scale == 1.0
    assert points[0].precision is None
    assert points[0].unit_of_measurement is None


def test_parse_scale_and_precision_set() -> None:
    raw = [
        {
            "key": "ai1",
            "name": "AI1",
            "platform": "sensor",
            "kind": "holding",
            "address": 0,
            "scale": 0.1,
            "precision": 2,
            "unit_of_measurement": "V",
            "device_class": "voltage",
        }
    ]
    point = _parse_points(raw)[0]
    assert point.scale == 0.1
    assert point.precision == 2
    assert point.unit_of_measurement == "V"
    assert point.device_class == "voltage"


# ---------------------------------------------------------------------------
# async_setup_entry / async_unload_entry – integration tests with HA harness
# ---------------------------------------------------------------------------


async def test_setup_entry_connection_fails(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    with patch("custom_components.siemens_logo.AsyncModbusTcpClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        await hass.config_entries.async_setup(config_entry.entry_id)

    assert config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_setup_entry_success(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_modbus_client: AsyncMock
) -> None:
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.siemens_logo.AsyncModbusTcpClient",
        return_value=mock_modbus_client,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)

    assert config_entry.state == ConfigEntryState.LOADED
    assert config_entry.entry_id in hass.data[DOMAIN]


async def test_setup_entry_no_points_still_loads(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.168.1.100", "port": 502, "unit_id": 1},
        options={"scan_interval": 10, "points": []},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.siemens_logo.AsyncModbusTcpClient",
    ) as mock_cls:
        mock_client = AsyncMock()
        mock_client.connected = True
        mock_client.connect = AsyncMock(return_value=True)
        mock_cls.return_value = mock_client

        with patch.object(
            SiemensLogoCoordinator,
            "async_config_entry_first_refresh",
            new=AsyncMock(return_value=None),
        ):
            await hass.config_entries.async_setup(entry.entry_id)

    assert entry.state == ConfigEntryState.LOADED


async def test_unload_entry(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_modbus_client: AsyncMock
) -> None:
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.siemens_logo.AsyncModbusTcpClient",
        return_value=mock_modbus_client,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)

    assert config_entry.state == ConfigEntryState.LOADED

    result = await hass.config_entries.async_unload(config_entry.entry_id)

    assert result is True
    assert config_entry.entry_id not in hass.data.get(DOMAIN, {})
    mock_modbus_client.close.assert_called_once()
