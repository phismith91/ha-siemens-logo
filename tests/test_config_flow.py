from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.siemens_logo.const import (
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

_POINTS_JSON = json.dumps(
    [{"key": "q1", "name": "Q1", "platform": "switch", "kind": "coil", "address": 8192}]
)


# ---------------------------------------------------------------------------
# User step
# ---------------------------------------------------------------------------


async def test_user_step_shows_form(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_user_step_creates_entry(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.100", CONF_PORT: 502, CONF_UNIT_ID: 1},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_HOST] == "192.168.1.100"
    assert result["data"][CONF_PORT] == 502
    assert result["options"][CONF_SCAN_INTERVAL] == DEFAULT_SCAN_INTERVAL


async def test_user_step_aborts_on_duplicate(hass: HomeAssistant) -> None:
    # first entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.100", CONF_PORT: 502, CONF_UNIT_ID: 1},
    )
    # second attempt with same host:port
    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={CONF_HOST: "192.168.1.100", CONF_PORT: 502, CONF_UNIT_ID: 1},
    )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# Options flow – init step (source selector)
# ---------------------------------------------------------------------------


async def test_options_init_shows_source_selector(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_init_manual_goes_to_manual_step(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SCAN_INTERVAL: 10, CONF_POINTS_SOURCE: POINTS_SOURCE_MANUAL},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "manual"


async def test_options_init_file_goes_to_file_step(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SCAN_INTERVAL: 10, CONF_POINTS_SOURCE: POINTS_SOURCE_FILE},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "file"


async def test_options_init_logo8_default_creates_entry(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SCAN_INTERVAL: 30, CONF_POINTS_SOURCE: POINTS_SOURCE_LOGO8_DEFAULT},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_POINTS] == LOGO8_DEFAULT_POINTS
    assert len(result["data"][CONF_POINTS]) > 20


# ---------------------------------------------------------------------------
# Options flow – manual step
# ---------------------------------------------------------------------------


async def _to_manual(hass, config_entry):
    config_entry.add_to_hass(hass)
    r = await hass.config_entries.options.async_init(config_entry.entry_id)
    return await hass.config_entries.options.async_configure(
        r["flow_id"],
        user_input={CONF_SCAN_INTERVAL: 10, CONF_POINTS_SOURCE: POINTS_SOURCE_MANUAL},
    )


async def test_manual_step_valid_json_creates_entry(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    result = await _to_manual(hass, config_entry)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_POINTS: _POINTS_JSON}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert isinstance(result["data"][CONF_POINTS], list)


async def test_manual_step_invalid_json_shows_error(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    result = await _to_manual(hass, config_entry)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_POINTS: "not valid json {{"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"].get(CONF_POINTS) == "invalid_json"


async def test_manual_step_non_list_shows_error(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    result = await _to_manual(hass, config_entry)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_POINTS: '{"key": "q1"}'}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"].get(CONF_POINTS) == "invalid_json"


# ---------------------------------------------------------------------------
# Options flow – file step
# ---------------------------------------------------------------------------


async def _to_file(hass, config_entry):
    config_entry.add_to_hass(hass)
    r = await hass.config_entries.options.async_init(config_entry.entry_id)
    return await hass.config_entries.options.async_configure(
        r["flow_id"],
        user_input={CONF_SCAN_INTERVAL: 10, CONF_POINTS_SOURCE: POINTS_SOURCE_FILE},
    )


async def test_file_step_valid_file_creates_entry(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    points = [{"key": "q1", "name": "Q1", "platform": "switch", "kind": "coil", "address": 8192}]
    result = await _to_file(hass, config_entry)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", dir=hass.config.config_dir, delete=False
    ) as f:
        json.dump(points, f)
        file_name = Path(f.name).name

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_FILE_PATH: file_name}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_POINTS] == points


async def test_file_step_missing_file_shows_error(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    result = await _to_file(hass, config_entry)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_FILE_PATH: "does_not_exist_xyz.json"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"].get(CONF_FILE_PATH) == "file_not_found"


async def test_file_step_invalid_json_shows_error(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    result = await _to_file(hass, config_entry)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", dir=hass.config.config_dir, delete=False
    ) as f:
        f.write("this is not json")
        file_name = Path(f.name).name

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_FILE_PATH: file_name}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"].get(CONF_FILE_PATH) == "invalid_json"
    assert result["data"][CONF_SCAN_INTERVAL] == 60
    assert isinstance(result["data"][CONF_POINTS], list)
