import json
from pathlib import Path


def test_manifest_domain_and_flow() -> None:
    manifest_path = Path("custom_components/siemens_logo/manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["domain"] == "siemens_logo"
    assert manifest["config_flow"] is True
    assert "pymodbus==3.8.3" in manifest["requirements"]
