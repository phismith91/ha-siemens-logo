from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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
    points: list[LogoPoint] = [p for p in data["points"] if p.platform == "sensor"]
    async_add_entities([LogoSensor(coordinator, entry.entry_id, point) for point in points])


class LogoSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str, point: LogoPoint) -> None:
        super().__init__(coordinator)
        self._point = point
        self._attr_unique_id = f"{entry_id}_{point.key}"
        self._attr_name = point.name
        self._attr_native_unit_of_measurement = point.unit_of_measurement
        self._attr_device_class = point.device_class

    @property
    def native_value(self):
        raw = self.coordinator.data.get(self._point.key)
        if raw is None:
            return None

        value = float(raw) * self._point.scale
        if self._point.precision is not None:
            value = round(value, self._point.precision)
        return value
