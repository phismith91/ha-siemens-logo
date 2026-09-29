# Napkin Runbook

## Curation Rules

- Re-prioritize on every read.
- Keep recurring, high-value notes only.
- Max 10 items per category.
- Each item includes date + "Do instead".

## Execution & Validation (Highest Priority)

1. **[2026-08-11] No fixed I/Q/M→VM mapping exists on LOGO! 8**
   Do instead: confirmed via research — local I/Q/M are NOT exposed as Modbus coils by any fixed address. Only VM addresses the user explicitly assigned via Network Input/Output blocks in their own LOGO!Soft Comfort program are reachable. CSV `address` column = raw VM address only, no symbolic I1/Q3/M12 lookup table. Source: [industrialmonitordirect.com](https://industrialmonitordirect.com/blogs/knowledgebase/siemens-logo-modbus-tcpip-io-addressing-and-function-codes).

## Shell & Command Reliability

1. **[2026-08-11] SSH agent died mid-session -> git push over SSH fails with "Permission denied (publickey)"**
   Do instead: check `ls -la /run/user/1000/vscode-ssh-auth-sock-*` — if the symlink target socket is missing, the VSCode host connection dropped (same root cause as Write/Read tool PreToolUse hook timeouts). Fix: `gh auth setup-git && git remote set-url origin https://github.com/phismith91/ha-siemens-logo.git` — pushes over HTTPS using gh's stored token, no SSH agent needed. Repo currently on this HTTPS remote as of 2026-08-11; switch back to SSH only if the agent proves stable again.
2. **[2026-08-11] Repo bootstrap on this VPS**
   Do instead: local dir `/home/philipp/projects/logo`, GitHub repo `phismith91/ha-siemens-logo`, `gh` already authenticated as phismith91.

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
4. **[2026-09-29] Sphinx-Needs docs replace docs/superpowers/**
   Do instead: specs go to `docs/specs/YYYY-MM-DD-<topic>-design.rst`
   (`spec::` objects linking `req::` IDs), plans go to
   `docs/plans/YYYY-MM-DD-<topic>.rst` (plain RST, condensed for large
   plans — see the note at the top of
   `docs/plans/2026-08-11-siemens-logo-integration.rst` for the pattern).
   Requirements live in `docs/requirements/index.rst` as `req::` objects.
   Tests get `test::` objects in `docs/tests/index.rst` linking to the
   `spec::`/`req::` IDs they verify. ubCode (VS Code extension) config:
   `ubproject.toml` at repo root, `[source] dir = "docs"`. Build check:
   `sphinx-build -b html docs docs/_build/html -W`.
