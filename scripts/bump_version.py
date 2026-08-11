"""Bump version in manifest.json und CHANGELOG.md.

Verwendung:
    python scripts/bump_version.py 1.2.3
    python scripts/bump_version.py 1.2.3-beta.1
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MANIFEST = Path("custom_components/siemens_logo/manifest.json")
CHANGELOG = Path("CHANGELOG.md")

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?$")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <version>", file=sys.stderr)
        print("Examples: 1.2.3   1.2.3-beta.1   1.2.3-rc.1", file=sys.stderr)
        return 1

    new_version = sys.argv[1].lstrip("v")
    if not VERSION_RE.match(new_version):
        print(f"Invalid version format: {new_version!r}", file=sys.stderr)
        print("Expected: 1.2.3  or  1.2.3-beta.1  or  1.2.3-rc.1", file=sys.stderr)
        return 1

    # --- manifest.json ---
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    old_version = manifest.get("version", "?")
    manifest["version"] = new_version
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"manifest.json: {old_version!r} → {new_version!r}")

    # --- CHANGELOG.md: [Unreleased] → [new_version] ---
    changelog = CHANGELOG.read_text(encoding="utf-8")
    from datetime import date

    today = date.today().isoformat()
    updated = changelog.replace(
        "## [Unreleased]",
        f"## [Unreleased]\n\n---\n\n## [{new_version}] – {today}",
        1,
    )
    CHANGELOG.write_text(updated, encoding="utf-8")
    print(f"CHANGELOG.md: [Unreleased] section promoted to [{new_version}]")

    print(f"\nNext steps:")
    print(f"  git add {MANIFEST} {CHANGELOG}")
    print(f'  git commit -m "chore(release): v{new_version}"')
    print(f"  git tag v{new_version}")
    print(f"  git push origin HEAD --tags")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
