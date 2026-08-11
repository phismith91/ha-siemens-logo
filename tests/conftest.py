from __future__ import annotations

import logging
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

try:
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    pytest_plugins = "pytest_homeassistant_custom_component"

    from custom_components.siemens_logo.const import (
        CONF_HOST,
        CONF_POINTS,
        CONF_PORT,
        CONF_SCAN_INTERVAL,
        CONF_UNIT_ID,
        DOMAIN,
    )
    from custom_components.siemens_logo.coordinator import SiemensLogoCoordinator
    from custom_components.siemens_logo.models import LogoPoint

    _HA_AVAILABLE = True
except ModuleNotFoundError:
    _HA_AVAILABLE = False

# reusable raw-point list (used inside conftest fixtures only)
_POINTS_RAW: list[dict] = [
    {"key": "q1", "name": "Q1", "platform": "switch", "kind": "coil", "address": 8192},
    {"key": "i1", "name": "I1", "platform": "binary_sensor", "kind": "discrete", "address": 1},
    {
        "key": "ai1",
        "name": "AI1",
        "platform": "sensor",
        "kind": "holding",
        "address": 0,
        "scale": 0.1,
        "precision": 1,
        "unit_of_measurement": "V",
    },
]


def make_coil_response(value: bool = False) -> MagicMock:
    r = MagicMock()
    r.isError.return_value = False
    r.bits = [value]
    return r


def make_register_response(value: int = 0) -> MagicMock:
    r = MagicMock()
    r.isError.return_value = False
    r.registers = [value]
    return r


def make_error_response() -> MagicMock:
    r = MagicMock()
    r.isError.return_value = True
    return r


@pytest.fixture
def mock_modbus_client() -> AsyncMock:
    client = AsyncMock()
    client.connected = True
    client.connect = AsyncMock(return_value=True)
    client.close = MagicMock()
    client.read_coils = AsyncMock(return_value=make_coil_response())
    client.read_discrete_inputs = AsyncMock(return_value=make_coil_response())
    client.read_holding_registers = AsyncMock(return_value=make_register_response())
    client.read_input_registers = AsyncMock(return_value=make_register_response())
    client.write_coil = AsyncMock(return_value=make_coil_response())
    return client


@pytest.fixture
def mock_coordinator() -> MagicMock:
    coord = MagicMock()
    coord.data = {}
    coord.async_add_listener = MagicMock(return_value=lambda: None)
    coord.async_set_coil = AsyncMock()
    coord.async_request_refresh = AsyncMock()
    return coord


if _HA_AVAILABLE:

    @pytest.fixture
    def config_entry() -> "MockConfigEntry":
        return MockConfigEntry(
            domain=DOMAIN,
            data={CONF_HOST: "192.168.1.100", CONF_PORT: 502, CONF_UNIT_ID: 1},
            options={CONF_SCAN_INTERVAL: 10, CONF_POINTS: _POINTS_RAW},
        )

    @pytest.fixture
    def coordinator(hass, mock_modbus_client) -> "SiemensLogoCoordinator":
        return SiemensLogoCoordinator(
            hass=hass,
            logger=logging.getLogger("test"),
            name="test",
            update_interval=timedelta(seconds=10),
            client=mock_modbus_client,
            unit_id=1,
            points=[
                LogoPoint(key="q1", name="Q1", platform="switch", kind="coil", address=8192),
                LogoPoint(key="i1", name="I1", platform="binary_sensor", kind="discrete", address=1),
                LogoPoint(key="ai1", name="AI1", platform="sensor", kind="holding", address=0),
                LogoPoint(key="ai2", name="AI2", platform="sensor", kind="input", address=1),
            ],
        )
