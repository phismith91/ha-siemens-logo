from __future__ import annotations

from datetime import timedelta
import logging

from pymodbus.client import AsyncModbusTcpClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_HOST,
    CONF_POINTS,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import SiemensLogoCoordinator
from .models import LogoPoint

_LOGGER = logging.getLogger(__name__)


def _parse_points(raw_points: list[dict]) -> list[LogoPoint]:
    points: list[LogoPoint] = []
    for idx, row in enumerate(raw_points):
        try:
            point = LogoPoint(
                key=str(row["key"]),
                name=str(row["name"]),
                platform=str(row["platform"]),
                kind=str(row["kind"]),
                address=int(row["address"]),
                unit_of_measurement=(
                    str(row["unit_of_measurement"])
                    if row.get("unit_of_measurement") is not None
                    else None
                ),
                device_class=(
                    str(row["device_class"]) if row.get("device_class") is not None else None
                ),
                scale=float(row.get("scale", 1.0)),
                precision=(
                    int(row["precision"]) if row.get("precision") is not None else None
                ),
            )
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.warning("Ignoring invalid point at index %s: %s", idx, err)
            continue

        if point.platform not in {"sensor", "switch", "binary_sensor"}:
            _LOGGER.warning("Ignoring point with unsupported platform: %s", point.platform)
            continue

        if point.kind not in {"coil", "discrete", "holding", "input"}:
            _LOGGER.warning("Ignoring point with unsupported kind: %s", point.kind)
            continue

        points.append(point)

    return points


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    unit_id = entry.data[CONF_UNIT_ID]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    points = _parse_points(entry.options.get(CONF_POINTS, []))
    if not points:
        _LOGGER.warning("No points configured for %s. Integration will load without entities.", entry.title)

    client = AsyncModbusTcpClient(host=host, port=port)
    connected = await client.connect()
    if not connected:
        raise ConfigEntryNotReady(f"Cannot connect to Siemens LOGO at {host}:{port}")

    coordinator = SiemensLogoCoordinator(
        hass=hass,
        logger=_LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_interval=timedelta(seconds=scan_interval),
        client=client,
        unit_id=unit_id,
        points=points,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "points": points,
    }

    enabled_platforms: set[Platform] = {Platform(point.platform) for point in points}
    await hass.config_entries.async_forward_entry_setups(entry, list(enabled_platforms))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    entry_data = hass.data[DOMAIN][entry.entry_id]
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        client = entry_data["client"]
        client.close()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
