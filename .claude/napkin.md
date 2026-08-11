# Napkin

## Corrections
| Date | Source | What Went Wrong | What To Do Instead |
|------|--------|----------------|-------------------|

## User Preferences
- Sprache: Deutsch (Kommentare, Planung, Kommunikation)
- TDD-Ansatz: Red → Green → Refactor, kein Commit ohne grüne Tests

## Patterns That Work
- `LogoPoint` als `@dataclass(slots=True)` – einfach und typsicher
- `pytest-homeassistant-custom-component` für HA-spezifische Tests vorhanden

## Patterns That Don't Work
- (noch keine Einträge)

## Domain Notes
- Home Assistant Custom Component für Siemens LOGO via Modbus TCP
- Stack: Python 3.12, pymodbus 3.8.3, ruff/black/mypy, pytest-cov
- Coverage-Gate: 80 % global (pyproject.toml), Ziel laut Plan: 90 % global / 95 % kritische Module
- HACS-Onboarding geplant (hacs.json vorhanden, hacs/action in Pipeline vorgesehen)
- Kein CI/CD-Workflow (`.github/workflows/`) existiert noch – muss noch erstellt werden
- Testabdeckung aktuell sehr gering: nur test_const, test_manifest, test_models, test_tdd_policy
- Wichtige noch fehlende Tests: config_flow, coordinator, sensor, switch, binary_sensor
- `manifest.json` hat Platzhalter-URL (`your-org`) – muss vor HACS-Submit ersetzt werden
