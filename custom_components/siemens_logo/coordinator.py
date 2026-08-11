from __future__ import annotations

from collections.abc import Callable

from pymodbus.client import AsyncModbusTcpClient

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .models import LogoPoint


class SiemensLogoCoordinator(DataUpdateCoordinator[dict[str, int | bool | None]]):
    def __init__(
        self,
        hass: HomeAssistant,
        logger,
        name: str,
        update_interval,
        client: AsyncModbusTcpClient,
        unit_id: int,
        points: list[LogoPoint],
    ) -> None:
        super().__init__(hass, logger=logger, name=name, update_interval=update_interval)
        self.client = client
        self.unit_id = unit_id
        self.points = points

    async def _read_point(self, point: LogoPoint) -> int | bool | None:
        if point.kind == "coil":
            response = await self.client.read_coils(point.address, count=1, slave=self.unit_id)
            if response.isError():
                return None
            return bool(response.bits[0])

        if point.kind == "discrete":
            response = await self.client.read_discrete_inputs(
                point.address, count=1, slave=self.unit_id
            )
            if response.isError():
                return None
            return bool(response.bits[0])

        if point.kind == "holding":
            response = await self.client.read_holding_registers(
                point.address, count=1, slave=self.unit_id
            )
            if response.isError():
                return None
            return int(response.registers[0])

        if point.kind == "input":
            response = await self.client.read_input_registers(
                point.address, count=1, slave=self.unit_id
            )
            if response.isError():
                return None
            return int(response.registers[0])

        return None

    async def async_set_coil(self, address: int, value: bool) -> None:
        response = await self.client.write_coil(address, value, slave=self.unit_id)
        if response.isError():
            raise UpdateFailed(f"Cannot write coil {address}")

    async def _async_update_data(self) -> dict[str, int | bool | None]:
        if not self.client.connected:
            connected = await self.client.connect()
            if not connected:
                raise UpdateFailed("Modbus client disconnected and reconnect failed")

        values: dict[str, int | bool | None] = {}
        for point in self.points:
            values[point.key] = await self._read_point(point)

        return values
