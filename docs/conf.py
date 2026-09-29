project = "ha-siemens-logo"
copyright = "2026, phismith91"
author = "phismith91"

extensions = ["sphinx_needs"]

needs_types = [
    dict(directive="req", title="Requirement", prefix="REQ_", color="#BFD8D2", style="node"),
    dict(directive="spec", title="Specification", prefix="SPEC_", color="#FEDCD2", style="node"),
    dict(directive="test", title="Test", prefix="TEST_", color="#DF744A", style="node"),
]

exclude_patterns = ["_build"]

html_theme = "furo"
