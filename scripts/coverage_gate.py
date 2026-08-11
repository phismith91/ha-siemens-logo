from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

GLOBAL_MIN = 80.0
FILE_MIN = 70.0
CRITICAL_MIN = 85.0
CRITICAL_FILES = {
    "custom_components/siemens_logo/__init__.py",
    "custom_components/siemens_logo/config_flow.py",
    "custom_components/siemens_logo/coordinator.py",
}


def _to_pct(value: str) -> float:
    return round(float(value) * 100, 2)


def main() -> int:
    xml_path = Path("coverage.xml")
    if not xml_path.exists():
        print("coverage.xml not found", file=sys.stderr)
        return 2

    root = ET.parse(xml_path).getroot()
    global_line_rate = root.attrib.get("line-rate", "0")
    global_pct = _to_pct(global_line_rate)

    failures: list[str] = []
    if global_pct < GLOBAL_MIN:
        failures.append(f"Global coverage {global_pct}% is below {GLOBAL_MIN}%")

    classes = root.findall(".//class")
    per_file: dict[str, float] = {}
    for cls in classes:
        filename = cls.attrib.get("filename")
        line_rate = cls.attrib.get("line-rate")
        if not filename or line_rate is None:
            continue
        per_file[filename] = _to_pct(line_rate)

    for filename, pct in per_file.items():
        if pct < FILE_MIN:
            failures.append(f"{filename}: {pct}% is below per-file minimum {FILE_MIN}%")

    for critical in CRITICAL_FILES:
        pct = per_file.get(critical)
        if pct is None:
            failures.append(f"Critical file missing in coverage: {critical}")
            continue
        if pct < CRITICAL_MIN:
            failures.append(
                f"{critical}: {pct}% is below critical minimum {CRITICAL_MIN}%"
            )

    if failures:
        print("Coverage gate failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print(
        f"Coverage gate passed: global={global_pct}%, per-file>={FILE_MIN}%, "
        f"critical>={CRITICAL_MIN}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
