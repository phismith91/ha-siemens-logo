# Design: Sphinx-Needs Documentation with ubCode Support

**Date:** 2026-09-29
**Status:** Approved
**Repo:** https://github.com/phismith91/ha-siemens-logo

## Goal

Replace the plain-Markdown `docs/superpowers/` tree with a Sphinx-Needs
project under `docs/`, so the ubCode VS Code extension (useblocks) gets full
editor support — live diagnostics, autocomplete, go-to-definition, and a
live RST preview — and so requirements, design specs, and tests are linked
through explicit traceability instead of prose cross-references.

This is the last spec written under the old `docs/superpowers/specs/*.md`
convention. Every spec and plan written after this feature ships goes to
`docs/specs/*.rst` / `docs/plans/*.rst` instead (see "Workflow convention
change" below).

## Non-goals (v1)

- No automatic import of pytest test IDs into `test::` need objects. Test
  needs are written and linked by hand. An automated importer (e.g. walking
  `tests/*.py` and generating stub `test::` objects) is a later enhancement,
  not part of this change.
- No migration of git history — the old `docs/superpowers/*.md` files are
  removed in this branch's commits, not rewritten in place. Their content
  lives on in git history and in the new `.rst` files.
- No custom Sphinx theme development. Use `furo` as-is.
- No `impl::` need type. The chosen chain is `req -> spec -> test`
  (3-tier); adding `impl::` linking to individual code modules is deferred
  until the 3-tier chain proves insufficient.

## Architecture

```
docs/
  conf.py                              # Sphinx + sphinx-needs config, furo theme
  index.rst                            # toctree: requirements, specs, plans, tests
  requirements/
    index.rst                          # req:: objects for the LOGO! integration
  specs/
    index.rst
    2026-08-11-siemens-logo-integration-design.rst   # migrated, spec:: objects, links to req::
  plans/
    index.rst
    2026-08-11-siemens-logo-integration.rst          # migrated, plain RST (not a need type)
  tests/
    index.rst                          # test:: objects, links to spec::/req::
ubproject.toml                         # repo root; [source] dir = "docs"
requirements_docs.txt                  # sphinx, sphinx-needs, furo
.github/workflows/docs.yml             # build on push/PR, deploy to Pages on main
```

`docs/superpowers/` is removed; its two files are superseded by the `specs/`
and `plans/` trees above.

### Need types and traceability

Three need types, using `sphinx-needs`' built-in `req`, `spec`, `test`
directives (no custom `needs_types` beyond setting explicit `REQ_`/`SPEC_`/
`TEST_` ID prefixes for readability):

- `req::` — what/why. One per functional requirement of the LOGO!
  integration (e.g. "connection setup with dedup", "CSV import
  idempotency", "chunked Modbus reads respect the 2000-coil limit"),
  extracted from the existing design spec's Architecture/Setup
  flow/Entities/Error handling sections.
- `spec::` — how. The migrated design doc's technical content, `:links:`
  back to the `req::` IDs it satisfies.
- `test::` — verification. One object per test module (or per logical test
  group within a module), naming the pytest file and referencing the test
  function names in its body, `:links:` to the `spec::`/`req::` IDs it
  covers.

Links are one-directional (`test` links to `spec`/`req`, `spec` links to
`req`) using `sphinx-needs`' default `:links:` field; `sphinx-needs`
auto-generates the reverse "linked by" view, so no manual back-links are
needed.

### ubCode setup

`ubproject.toml` at the repo root:

```toml
"$schema" = "https://ubcode.useblocks.com/ubproject.schema.json"

[project]
name = "ha-siemens-logo"

[source]
dir = "docs"
```

This is enough for the extension to index the project once installed; no
per-user VS Code settings are added (installing the extension itself is a
manual step for whoever opens the repo in VS Code).

### Sphinx config

`docs/conf.py`: minimal, `extensions = ["sphinx_needs"]`, `furo` HTML theme,
`needs_types` with explicit `REQ_`/`SPEC_`/`TEST_` prefixes,
`needs_id_regex` left at the sphinx-needs default.

## Workflow convention change

The project's napkin directive ("Use full superpowers workflow for this
project") stays in force, but the artifact format changes:

- Old: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`,
  `docs/superpowers/plans/YYYY-MM-DD-<topic>.md` (plain Markdown).
- New: `docs/specs/YYYY-MM-DD-<topic>-design.rst`,
  `docs/plans/YYYY-MM-DD-<topic>.rst` (RST; specs use `spec::`/`req::`
  objects where the content states a requirement or technical design
  decision, plans stay plain narrative RST).

This is recorded in `.claude/napkin.md` under "User Directives" so future
sessions pick it up automatically.

## CI/CD

New `.github/workflows/docs.yml`:

- Trigger: `push` to `main`, and `pull_request` (build-only, no deploy).
- Steps: checkout, set up Python, `pip install -r requirements_docs.txt`,
  `sphinx-build -b html docs docs/_build/html -W` (warnings fail the
  build — this is the change's verification check, since there's no
  application code to unit-test here).
- Deploy step (main only): `actions/upload-pages-artifact` +
  `actions/deploy-pages`, the official GitHub Actions Pages flow (no
  third-party action, no deploy token to manage).

This is a separate workflow file, additive to the existing
`pre-commit.yml` / `test.yml` / `validate-hacs.yml` /
`validate-hassfest.yml` / `release.yml` — none of those are touched.

**Manual one-time step (user, not this change):** GitHub repo Settings ->
Pages -> Source must be set to "GitHub Actions". This can't be done via
git/CI config and is called out again at hand-off.

## Testing (verification)

No application code changes, so no pytest additions. Verification is:

- `sphinx-build -b html docs docs/_build/html -W` passes locally before
  commit (catches malformed RST, broken `:links:` targets, duplicate need
  IDs).
- The same command running green in `docs.yml` on the PR.

## Migration steps (for the implementation plan)

1. Add `ubproject.toml`, `requirements_docs.txt`.
2. Scaffold `docs/conf.py` and the `index.rst` toctree skeleton.
3. Write `requirements/index.rst` (`req::` objects extracted from the old
   design spec).
4. Migrate `specs/2026-08-11-siemens-logo-integration-design.md` ->
   `specs/2026-08-11-siemens-logo-integration-design.rst` as `spec::`
   objects linking to the new `req::` IDs.
5. Migrate `plans/2026-08-11-siemens-logo-integration.md` ->
   `plans/2026-08-11-siemens-logo-integration.rst` as plain RST.
6. Write `tests/index.rst` (`test::` objects for each existing
   `tests/test_*.py` module, linked to the relevant `spec::`/`req::` IDs).
7. Remove `docs/superpowers/`.
8. Add `.github/workflows/docs.yml`.
9. Update `.claude/napkin.md` with the workflow convention change.
10. Verify `sphinx-build -W` locally, commit, open PR.
