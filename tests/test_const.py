from custom_components.siemens_logo.const import (
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DOMAIN,
    LOGO8_DEFAULT_POINTS,
    PLATFORMS,
    POINTS_SOURCE_FILE,
    POINTS_SOURCE_LOGO8_DEFAULT,
    POINTS_SOURCE_MANUAL,
)


def test_defaults_are_stable() -> None:
    assert DOMAIN == "siemens_logo"
    assert DEFAULT_PORT == 502
    assert DEFAULT_UNIT_ID == 1
    assert DEFAULT_SCAN_INTERVAL == 10


def test_platforms_supported() -> None:
    assert sorted(PLATFORMS) == ["binary_sensor", "sensor", "switch"]


def test_points_source_constants() -> None:
    assert POINTS_SOURCE_MANUAL == "manual"
    assert POINTS_SOURCE_FILE == "file"
    assert POINTS_SOURCE_LOGO8_DEFAULT == "logo8_default"


def test_logo8_default_points_structure() -> None:
    assert len(LOGO8_DEFAULT_POINTS) > 20
    keys = {p["key"] for p in LOGO8_DEFAULT_POINTS}
    # alle digitalen I/Os vorhanden
    assert "i1" in keys and "i8" in keys
    assert "q1" in keys and "q8" in keys
    assert "ai1" in keys and "ai8" in keys
    assert "m1" in keys
    # keine doppelten Keys
    assert len(keys) == len(LOGO8_DEFAULT_POINTS)
    # alle Plattformen gültig
    valid_platforms = {"sensor", "switch", "binary_sensor"}
    assert all(p["platform"] in valid_platforms for p in LOGO8_DEFAULT_POINTS)
