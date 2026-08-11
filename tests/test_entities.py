from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.siemens_logo.binary_sensor import LogoBinarySensor
from custom_components.siemens_logo.models import LogoPoint
from custom_components.siemens_logo.sensor import LogoSensor
from custom_components.siemens_logo.switch import LogoSwitch


def _make_coord(data: dict) -> MagicMock:
    coord = MagicMock()
    coord.data = data
    coord.async_add_listener = MagicMock(return_value=lambda: None)
    coord.async_set_coil = AsyncMock()
    coord.async_request_refresh = AsyncMock()
    return coord


# ---------------------------------------------------------------------------
# LogoSensor
# ---------------------------------------------------------------------------


def test_sensor_native_value_applies_scale_and_precision() -> None:
    point = LogoPoint(
        key="ai1", name="AI1", platform="sensor", kind="holding", address=0,
        scale=0.1, precision=1, unit_of_measurement="V",
    )
    sensor = LogoSensor(_make_coord({"ai1": 250}), "entry_id", point)
    assert sensor.native_value == 25.0


def test_sensor_native_value_no_precision() -> None:
    point = LogoPoint(key="ai1", name="AI1", platform="sensor", kind="holding", address=0, scale=2.0)
    sensor = LogoSensor(_make_coord({"ai1": 3}), "entry_id", point)
    assert sensor.native_value == 6.0


def test_sensor_native_value_none_when_coordinator_has_no_data() -> None:
    point = LogoPoint(key="ai1", name="AI1", platform="sensor", kind="holding", address=0)
    sensor = LogoSensor(_make_coord({"ai1": None}), "entry_id", point)
    assert sensor.native_value is None


def test_sensor_unique_id_and_name() -> None:
    point = LogoPoint(key="ai1", name="Analog In 1", platform="sensor", kind="holding", address=0)
    sensor = LogoSensor(_make_coord({}), "my_entry", point)
    assert sensor.unique_id == "my_entry_ai1"
    assert sensor.name == "Analog In 1"


def test_sensor_unit_and_device_class_forwarded() -> None:
    point = LogoPoint(
        key="ai1", name="AI1", platform="sensor", kind="holding", address=0,
        unit_of_measurement="V", device_class="voltage",
    )
    sensor = LogoSensor(_make_coord({}), "entry_id", point)
    assert sensor.native_unit_of_measurement == "V"
    assert sensor.device_class == "voltage"


# ---------------------------------------------------------------------------
# LogoSwitch
# ---------------------------------------------------------------------------


def test_switch_is_on_true() -> None:
    point = LogoPoint(key="q1", name="Q1", platform="switch", kind="coil", address=8192)
    switch = LogoSwitch(_make_coord({"q1": True}), "entry_id", point)
    assert switch.is_on is True


def test_switch_is_on_false() -> None:
    point = LogoPoint(key="q1", name="Q1", platform="switch", kind="coil", address=8192)
    switch = LogoSwitch(_make_coord({"q1": False}), "entry_id", point)
    assert switch.is_on is False


def test_switch_is_on_none_when_missing() -> None:
    point = LogoPoint(key="q1", name="Q1", platform="switch", kind="coil", address=8192)
    switch = LogoSwitch(_make_coord({"q1": None}), "entry_id", point)
    assert switch.is_on is None


async def test_switch_turn_on_calls_set_coil() -> None:
    point = LogoPoint(key="q1", name="Q1", platform="switch", kind="coil", address=8192)
    coord = _make_coord({"q1": False})
    switch = LogoSwitch(coord, "entry_id", point)
    await switch.async_turn_on()
    coord.async_set_coil.assert_awaited_once_with(8192, True)
    coord.async_request_refresh.assert_awaited_once()


async def test_switch_turn_off_calls_set_coil() -> None:
    point = LogoPoint(key="q1", name="Q1", platform="switch", kind="coil", address=8192)
    coord = _make_coord({"q1": True})
    switch = LogoSwitch(coord, "entry_id", point)
    await switch.async_turn_off()
    coord.async_set_coil.assert_awaited_once_with(8192, False)
    coord.async_request_refresh.assert_awaited_once()


# ---------------------------------------------------------------------------
# LogoBinarySensor
# ---------------------------------------------------------------------------


def test_binary_sensor_is_on_true() -> None:
    point = LogoPoint(key="i1", name="I1", platform="binary_sensor", kind="discrete", address=1)
    bs = LogoBinarySensor(_make_coord({"i1": True}), "entry_id", point)
    assert bs.is_on is True


def test_binary_sensor_is_on_false() -> None:
    point = LogoPoint(key="i1", name="I1", platform="binary_sensor", kind="discrete", address=1)
    bs = LogoBinarySensor(_make_coord({"i1": False}), "entry_id", point)
    assert bs.is_on is False


def test_binary_sensor_is_on_none_when_missing() -> None:
    point = LogoPoint(key="i1", name="I1", platform="binary_sensor", kind="discrete", address=1)
    bs = LogoBinarySensor(_make_coord({"i1": None}), "entry_id", point)
    assert bs.is_on is None


def test_binary_sensor_device_class_forwarded() -> None:
    point = LogoPoint(
        key="i1", name="I1", platform="binary_sensor", kind="discrete", address=1,
        device_class="motion",
    )
    bs = LogoBinarySensor(_make_coord({}), "entry_id", point)
    assert bs.device_class == "motion"
