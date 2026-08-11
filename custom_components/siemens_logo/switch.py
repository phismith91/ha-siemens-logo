from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .models import LogoPoint


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    points: list[LogoPoint] = [p for p in data["points"] if p.platform == "switch"]
    async_add_entities([LogoSwitch(coordinator, entry.entry_id, point) for point in points])


class LogoSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str, point: LogoPoint) -> None:
        super().__init__(coordinator)
        self._point = point
        self._attr_unique_id = f"{entry_id}_{point.key}"
        self._attr_name = point.name

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get(self._point.key)
        if value is None:
            return None
        return bool(value)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_coil(self._point.address, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_coil(self._point.address, False)
        await self.coordinator.async_request_refresh()
