from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_FILE_PATH,
    CONF_HOST,
    CONF_POINTS,
    CONF_POINTS_SOURCE,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DOMAIN,
    LOGO8_DEFAULT_POINTS,
    POINTS_SOURCE_FILE,
    POINTS_SOURCE_LOGO8_DEFAULT,
    POINTS_SOURCE_MANUAL,
)

DEFAULT_POINTS = [
    {
        "key": "q1",
        "name": "LOGO Q1",
        "platform": "switch",
        "kind": "coil",
        "address": 8192,
    },
    {
        "key": "i1",
        "name": "LOGO I1",
        "platform": "binary_sensor",
        "kind": "discrete",
        "address": 1,
    },
    {
        "key": "ai1",
        "name": "LOGO AI1",
        "platform": "sensor",
        "kind": "holding",
        "address": 0,
        "scale": 0.1,
        "precision": 1,
        "unit_of_measurement": "V",
    },
]


class SiemensLogoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Siemens LOGO {user_input[CONF_HOST]}",
                data=user_input,
                options={
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                    CONF_POINTS: DEFAULT_POINTS,
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): NumberSelector(
                    NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): NumberSelector(
                    NumberSelectorConfig(min=1, max=255, mode=NumberSelectorMode.BOX)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return SiemensLogoOptionsFlow(config_entry)


class SiemensLogoOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
        self._scan_interval: int = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Quelle für die Punkte-Konfiguration wählen."""
        if user_input is not None:
            self._scan_interval = int(user_input[CONF_SCAN_INTERVAL])
            source = user_input[CONF_POINTS_SOURCE]
            if source == POINTS_SOURCE_MANUAL:
                return await self.async_step_manual()
            if source == POINTS_SOURCE_FILE:
                return await self.async_step_file()
            # logo8_default: sofort speichern
            return self.async_create_entry(
                title="",
                data={CONF_SCAN_INTERVAL: self._scan_interval, CONF_POINTS: LOGO8_DEFAULT_POINTS},
            )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self._scan_interval,
                ): NumberSelector(NumberSelectorConfig(min=1, max=3600, mode=NumberSelectorMode.BOX)),
                vol.Required(CONF_POINTS_SOURCE, default=POINTS_SOURCE_MANUAL): SelectSelector(
                    SelectSelectorConfig(
                        options=[POINTS_SOURCE_MANUAL, POINTS_SOURCE_FILE, POINTS_SOURCE_LOGO8_DEFAULT],
                        mode=SelectSelectorMode.LIST,
                        translation_key=CONF_POINTS_SOURCE,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Points direkt als JSON eingeben."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                points = json.loads(user_input[CONF_POINTS])
                if not isinstance(points, list):
                    raise ValueError("points must be a list")
            except (json.JSONDecodeError, ValueError):
                errors[CONF_POINTS] = "invalid_json"
            else:
                return self.async_create_entry(
                    title="",
                    data={CONF_SCAN_INTERVAL: self._scan_interval, CONF_POINTS: points},
                )

        current_points = self.config_entry.options.get(CONF_POINTS, [])
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POINTS,
                    default=json.dumps(current_points, ensure_ascii=True, indent=2),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True)),
            }
        )
        return self.async_show_form(step_id="manual", data_schema=schema, errors=errors)

    async def async_step_file(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Points aus einer JSON-Datei im HA-Konfigurationsverzeichnis laden.

        Beispiel: custom_components/siemens_logo/my_points.json
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            raw_path = user_input[CONF_FILE_PATH].strip()
            full_path = Path(self.hass.config.path(raw_path))
            try:
                content = await self.hass.async_add_executor_job(
                    functools.partial(full_path.read_text, encoding="utf-8")
                )
                points = json.loads(content)
                if not isinstance(points, list):
                    raise ValueError("points must be a list")
            except FileNotFoundError:
                errors[CONF_FILE_PATH] = "file_not_found"
            except (json.JSONDecodeError, ValueError):
                errors[CONF_FILE_PATH] = "invalid_json"
            else:
                return self.async_create_entry(
                    title="",
                    data={CONF_SCAN_INTERVAL: self._scan_interval, CONF_POINTS: points},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_FILE_PATH): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
            }
        )
        return self.async_show_form(step_id="file", data_schema=schema, errors=errors)
