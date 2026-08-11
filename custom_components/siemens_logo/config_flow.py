from __future__ import annotations

import json
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_HOST,
    CONF_POINTS,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DOMAIN,
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

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            points_raw = user_input[CONF_POINTS]
            try:
                points = json.loads(points_raw)
                if not isinstance(points, list):
                    raise ValueError("points must be a list")
            except (json.JSONDecodeError, ValueError):
                errors[CONF_POINTS] = "invalid_json"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                        CONF_POINTS: points,
                    },
                )

        points = self.config_entry.options.get(CONF_POINTS, DEFAULT_POINTS)
        points_json = json.dumps(points, ensure_ascii=True, indent=2)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): NumberSelector(NumberSelectorConfig(min=1, max=3600, mode=NumberSelectorMode.BOX)),
                vol.Required(CONF_POINTS, default=points_json): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
