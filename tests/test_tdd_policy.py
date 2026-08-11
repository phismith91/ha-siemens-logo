from pathlib import Path


def test_plan_mentions_tdd() -> None:
    plan = Path("PLAN-CI-CD-TDD-HACS.md").read_text(encoding="utf-8")

    assert "Test Driven Development" in plan
    assert "Red" in plan
    assert "Green" in plan
    assert "Refactor" in plan
