# Napkin Runbook

## Curation Rules
- Re-prioritize on every read.
- Keep recurring, high-value notes only.
- Max 10 items per category.
- Each item includes date + "Do instead".

## Execution & Validation (Highest Priority)
1. **[2026-08-11] LOGO! 8 fixed I/Q/M→VM mapping is unverified**
   Do instead: before hardcoding the symbolic-address (I1/Q3/M12) → VM-offset lookup table, confirm exact addresses against the Siemens 0BA8 manual. Don't ship guessed offsets.

## Shell & Command Reliability
1. **[2026-08-11] Repo bootstrap on this VPS**
   Do instead: local dir `/home/philipp/projects/logo`, GitHub repo `phismith91/ha-siemens-logo`, `gh` already authenticated as phismith91, SSH git protocol.

## Domain Behavior Guardrails
1. **[2026-08-11] .lsc binary import is out of scope for v1**
   Do instead: v1 config uses CSV import (name,address,type) via HA's native FileSelector. Only attempt `.lsc` parsing in a later phase, and only after inspecting a real sample file for feasibility.

## User Directives
1. **[2026-08-11] Use full superpowers workflow for this project**
   Do instead: brainstorming → spec doc → writing-plans → TDD → code-review → finishing-a-development-branch, for every feature, every session.
2. **[2026-08-11] Feature branches only, never push to master** (from global memory `feedback_feature_branches`)
   Do instead: every feature/fix gets its own branch + PR, mirrors luxorliving workflow.
3. **[2026-08-11] Mirror luxorliving repo conventions**
   Do instead: pre-commit (black/isort/flake8/bandit/prettier), pytest + pytest-homeassistant-custom-component, validate-hacs + validate-hassfest CI jobs, release.yml on tag push (vX.Y.Z stable, vX.Y.Z-rc.N prerelease), CHANGELOG.md.
