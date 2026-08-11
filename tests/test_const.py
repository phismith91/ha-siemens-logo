from custom_components.siemens_logo.const import (
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DOMAIN,
    PLATFORMS,
)


def test_defaults_are_stable() -> None:
    assert DOMAIN == "siemens_logo"
    assert DEFAULT_PORT == 502
    assert DEFAULT_UNIT_ID == 1
    assert DEFAULT_SCAN_INTERVAL == 10


def test_platforms_supported() -> None:
    assert sorted(PLATFORMS) == ["binary_sensor", "sensor", "switch"]
