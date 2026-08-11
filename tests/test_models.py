from custom_components.siemens_logo.models import LogoPoint


def test_logo_point_defaults() -> None:
    point = LogoPoint(
        key="ai1",
        name="Analog In 1",
        platform="sensor",
        kind="holding",
        address=0,
    )

    assert point.scale == 1.0
    assert point.precision is None
    assert point.unit_of_measurement is None
    assert point.device_class is None
