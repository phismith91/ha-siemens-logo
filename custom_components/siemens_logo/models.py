from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LogoPoint:
    key: str
    name: str
    platform: str
    kind: str
    address: int
    unit_of_measurement: str | None = None
    device_class: str | None = None
    scale: float = 1.0
    precision: int | None = None
