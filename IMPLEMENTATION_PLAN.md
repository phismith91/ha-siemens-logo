# Implementierungsplan: Siemens LOGO HA Integration

Konkrete Umsetzungsschritte auf Basis des aktuellen Repo-Stands.
Reihenfolge: Tests zuerst (TDD), dann CI/CD, dann HACS-Readiness.

---

## Phase 1 – Test-Fundament (TDD)

**Ziel:** Coverage auf ≥ 80 % bringen (aktuelles Gate), kritische Module auf ≥ 95 %.

### 1.1 `tests/test_init.py` – `_parse_points` und `async_setup_entry`

| # | Test | Erwartetes Ergebnis |
|---|------|---------------------|
| 1 | `_parse_points` mit gültigem JSON | Liste von `LogoPoint`-Objekten |
| 2 | `_parse_points` – fehlende Pflichtfelder | Eintrag wird übersprungen, kein Absturz |
| 3 | `_parse_points` – ungültige platform/kind | Eintrag wird übersprungen |
| 4 | `async_setup_entry` – Verbindung schlägt fehl | `ConfigEntryNotReady` |
| 5 | `async_setup_entry` – Erfolgsfall (mock client) | `True`, Coordinator registriert |
| 6 | `async_unload_entry` | Platforms entladen, Client geschlossen |

### 1.2 `tests/test_coordinator.py` – `SiemensLogoCoordinator`

| # | Test | Erwartetes Ergebnis |
|---|------|---------------------|
| 1 | `_read_point` – kind=coil, Erfolg | `True`/`False` |
| 2 | `_read_point` – kind=discrete, Erfolg | `True`/`False` |
| 3 | `_read_point` – kind=holding, Erfolg | `int` |
| 4 | `_read_point` – kind=input, Erfolg | `int` |
| 5 | `_read_point` – Modbus-Error | `None` |
| 6 | `_async_update_data` – Client disconnected, Reconnect schlägt fehl | `UpdateFailed` |
| 7 | `_async_update_data` – Erfolg, alle Points gelesen | `dict[str, ...]` |
| 8 | `async_set_coil` – Modbus-Error | `UpdateFailed` |

### 1.3 `tests/test_config_flow.py` – `SiemensLogoConfigFlow`

| # | Test | Erwartetes Ergebnis |
|---|------|---------------------|
| 1 | `async_step_user` – zeigt Formular | `FlowResultType.FORM` |
| 2 | `async_step_user` – Erfolg | `FlowResultType.CREATE_ENTRY` |
| 3 | Options Flow – Scan-Intervall ändern | Options korrekt gespeichert |
| 4 | Options Flow – ungültiges Points-JSON | Fehler im Formular |

### 1.4 `tests/test_entities.py` – Sensor / Switch / Binary Sensor

| # | Test | Erwartetes Ergebnis |
|---|------|---------------------|
| 1 | Sensor: `native_value` mit scale + precision | Korrekt gerundeter Float |
| 2 | Sensor: `native_value` wenn Coordinator `None` liefert | `None` |
| 3 | Switch: `is_on` | `True`/`False` |
| 4 | Switch: `async_turn_on` / `async_turn_off` | Ruft `async_set_coil` auf |
| 5 | Binary Sensor: `is_on` | `True`/`False` |

---

## Phase 2 – CI/CD Pipeline (GitHub Actions)

**Ziel:** Alle Checks automatisiert, kein Merge auf `main` ohne grüne Pipeline.

### 2.1 `.github/workflows/ci.yml`

```
Trigger: push + pull_request auf main und feat/**, fix/**, chore/**

Jobs (sequenziell nur wo nötig):
  lint         → ruff check . + black --check .
  typecheck    → mypy custom_components/siemens_logo
  hassfest     → python -m script.hassfest  (HA-Checkout als Dependency)
  tests        → pytest (mit --cov, XML + HTML Artefakt)
  coverage-gate → scripts/coverage_gate.py (global 80%, kritisch 95%)
  hacs-validate → hacs/action@main
```

Detaillierte Job-Konfiguration: alle Jobs laufen auf `ubuntu-latest`, Python 3.12.

### 2.2 `.github/workflows/release.yml`

```
Trigger: push von Tag v*.*.*

Jobs:
  verify   → lint + tests + hassfest + hacs-validate (wiederholend)
  package  → Versionskonsistenz prüfen (manifest.json == hacs.json == tag)
  release  → gh release create mit autogenerierten Notes
```

### 2.3 `.github/workflows/nightly.yml`

```
Trigger: cron "0 3 * * *"

Jobs:
  regression → pytest gegen aktuelle HA stable + beta
```

---

## Phase 3 – Coverage-Steigerung

**Ziel:** Global ≥ 90 %, kritische Module ≥ 95 %.

Schritte:
1. `scripts/coverage_gate.py` um Modul-spezifische Prüfung erweitern (coordinator, config_flow, __init__)
2. `pyproject.toml`: `fail_under` von 80 → 90 hochziehen, sobald Phase 1 vollständig grün ist
3. Fehlende Edge-Cases in Coordinator und Config Flow nachschreiben (Reconnect-Timeout, gleichzeitige Updates)

---

## Phase 4 – HACS Readiness

**Ziel:** Repo ist direkt als HACS Custom Repository installierbar.

| Aufgabe | Datei | Aktion |
|---------|-------|--------|
| Echte Repo-URL eintragen | `manifest.json` | `"documentation"` + `"issue_tracker"` auf echten GitHub-Link setzen |
| HACS-Metadaten prüfen | `hacs.json` | `homeassistant` Mindestversion eintragen |
| Changelog anlegen | `CHANGELOG.md` | Eintragsformat für Release-Notes |
| Branch Protection | GitHub Settings | Pflichtchecks aus 2.1 aktivieren |

---

## Reihenfolge und Abhängigkeiten

```
Phase 1 (Tests)
  └── Phase 3 (Coverage hoch) ─ parallel nach 1.1–1.4
Phase 2 (CI/CD)
  └── kann parallel zu Phase 1 aufgebaut werden
      └── Phase 4 (HACS) erst wenn Phase 2 grün
```

## Offene Entscheidungen

- `pytest-asyncio`-Modus: `asyncio_mode = "auto"` in `pyproject.toml` eintragen?  
  → Erforderlich für Coordinator- und Entity-Tests mit `async def`.
- Soll `pytest-homeassistant-custom-component` die HA-Fixtures für Config Flow liefern, oder eigene Mocks?  
  → Empfehlung: HA-Fixtures nutzen (`hass`, `config_entry`), weniger Boilerplate.
