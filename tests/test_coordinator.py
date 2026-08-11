from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.siemens_logo.coordinator import SiemensLogoCoordinator
from custom_components.siemens_logo.models import LogoPoint


def _coil_resp(value: bool = True) -> MagicMock:
    r = MagicMock()
    r.isError.return_value = False
    r.bits = [value]
    return r


def _reg_resp(value: int = 42) -> MagicMock:
    r = MagicMock()
    r.isError.return_value = False
    r.registers = [value]
    return r


def _err_resp() -> MagicMock:
    r = MagicMock()
    r.isError.return_value = True
    return r


# ---------------------------------------------------------------------------
# _read_point
# ---------------------------------------------------------------------------


async def test_read_coil_returns_bool(coordinator: SiemensLogoCoordinator, mock_modbus_client: AsyncMock) -> None:
    mock_modbus_client.read_coils = AsyncMock(return_value=_coil_resp(True))
    point = LogoPoint(key="q1", name="Q1", platform="switch", kind="coil", address=8192)
    result = await coordinator._read_point(point)
    assert result is True
    mock_modbus_client.read_coils.assert_called_once_with(8192, count=1, slave=1)


async def test_read_discrete_returns_bool(coordinator: SiemensLogoCoordinator, mock_modbus_client: AsyncMock) -> None:
    mock_modbus_client.read_discrete_inputs = AsyncMock(return_value=_coil_resp(False))
    point = LogoPoint(key="i1", name="I1", platform="binary_sensor", kind="discrete", address=1)
    result = await coordinator._read_point(point)
    assert result is False


async def test_read_holding_returns_int(coordinator: SiemensLogoCoordinator, mock_modbus_client: AsyncMock) -> None:
    mock_modbus_client.read_holding_registers = AsyncMock(return_value=_reg_resp(250))
    point = LogoPoint(key="ai1", name="AI1", platform="sensor", kind="holding", address=0)
    result = await coordinator._read_point(point)
    assert result == 250


async def test_read_input_returns_int(coordinator: SiemensLogoCoordinator, mock_modbus_client: AsyncMock) -> None:
    mock_modbus_client.read_input_registers = AsyncMock(return_value=_reg_resp(99))
    point = LogoPoint(key="ai2", name="AI2", platform="sensor", kind="input", address=1)
    result = await coordinator._read_point(point)
    assert result == 99


async def test_read_point_modbus_error_returns_none(coordinator: SiemensLogoCoordinator, mock_modbus_client: AsyncMock) -> None:
    mock_modbus_client.read_coils = AsyncMock(return_value=_err_resp())
    point = LogoPoint(key="q1", name="Q1", platform="switch", kind="coil", address=8192)
    result = await coordinator._read_point(point)
    assert result is None


async def test_read_point_unknown_kind_returns_none(coordinator: SiemensLogoCoordinator) -> None:
    point = LogoPoint(key="x", name="X", platform="sensor", kind="coil", address=0)
    # Override kind after creation (slots=True, need workaround via object.__setattr__)
    object.__setattr__(point, "kind", "unknown")
    result = await coordinator._read_point(point)
    assert result is None


# ---------------------------------------------------------------------------
# _async_update_data
# ---------------------------------------------------------------------------


async def test_async_update_data_success(coordinator: SiemensLogoCoordinator, mock_modbus_client: AsyncMock) -> None:
    mock_modbus_client.read_coils = AsyncMock(return_value=_coil_resp(True))
    mock_modbus_client.read_discrete_inputs = AsyncMock(return_value=_coil_resp(False))
    mock_modbus_client.read_holding_registers = AsyncMock(return_value=_reg_resp(100))
    mock_modbus_client.read_input_registers = AsyncMock(return_value=_reg_resp(200))

    data = await coordinator._async_update_data()

    assert data["q1"] is True
    assert data["i1"] is False
    assert data["ai1"] == 100
    assert data["ai2"] == 200


async def test_async_update_data_reconnects_when_disconnected(
    coordinator: SiemensLogoCoordinator, mock_modbus_client: AsyncMock
) -> None:
    mock_modbus_client.connected = False
    mock_modbus_client.connect = AsyncMock(return_value=True)
    mock_modbus_client.read_coils = AsyncMock(return_value=_coil_resp(False))
    mock_modbus_client.read_discrete_inputs = AsyncMock(return_value=_coil_resp(False))
    mock_modbus_client.read_holding_registers = AsyncMock(return_value=_reg_resp(0))
    mock_modbus_client.read_input_registers = AsyncMock(return_value=_reg_resp(0))

    await coordinator._async_update_data()

    mock_modbus_client.connect.assert_called_once()


async def test_async_update_data_reconnect_fails_raises(
    coordinator: SiemensLogoCoordinator, mock_modbus_client: AsyncMock
) -> None:
    mock_modbus_client.connected = False
    mock_modbus_client.connect = AsyncMock(return_value=False)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


# ---------------------------------------------------------------------------
# async_set_coil
# ---------------------------------------------------------------------------


async def test_set_coil_success(coordinator: SiemensLogoCoordinator, mock_modbus_client: AsyncMock) -> None:
    mock_modbus_client.write_coil = AsyncMock(return_value=_coil_resp())
    await coordinator.async_set_coil(8192, True)
    mock_modbus_client.write_coil.assert_called_once_with(8192, True, slave=1)


async def test_set_coil_error_raises(coordinator: SiemensLogoCoordinator, mock_modbus_client: AsyncMock) -> None:
    mock_modbus_client.write_coil = AsyncMock(return_value=_err_resp())
    with pytest.raises(UpdateFailed):
        await coordinator.async_set_coil(8192, True)
