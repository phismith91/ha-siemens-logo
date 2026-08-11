# Plan: Volle CI/CD-Pipeline mit TDD und HACS-Gates

## Ziel

Dieser Plan definiert die Umsetzung fuer die Siemens-LOGO-Home-Assistant-Integration mit:

- Test Driven Development (TDD) als Standardprozess
- Voller CI/CD-Pipeline auf GitHub Actions
- Hoher Testabdeckung mit verpflichtenden Quality Gates
- HACS-relevanten Pruefungen in der Pipeline
- Reproduzierbarem Release-Prozess fuer spaeteres HACS-Onboarding

Es wird vor diesem Plan keine weitere Feature-Implementierung gestartet.

## Qualitaetsziele (Definition of Done)

- Unit- und Integrationstests fuer alle Kernmodule
- Mindestabdeckung:
  - Global: 90%
  - Kritische Module (Parser, Coordinator, Config Flow): 95%
- Keine Lint- oder Typing-Fehler
- HACS-Validierung erfolgreich
- Releases nur aus getaggten, voll geprueften Builds

## Entwicklungsprozess (TDD)

1. Red
- Vor jeder Funktion zuerst Test schreiben
- Test muss initial fehlschlagen

2. Green
- Minimalen Code implementieren, bis Test gruen ist

3. Refactor
- Code bereinigen, Struktur verbessern
- Tests bleiben gruen

4. Commit-Regel
- Kein Commit ohne gruenen lokalen Testlauf
- Kein Merge ohne gruene CI und Coverage-Gates

## Branch- und Merge-Strategie

- main: stabil, releasefaehig
- feat/*: neue Features
- fix/*: Bugfixes
- chore/*: CI/Build/Doku

Branch Protection fuer main:
- Pflichtchecks:
  - lint
  - typecheck
  - tests
  - coverage-gate
  - hacs-validate
  - hassfest
- Mindestens 1 Review
- Keine direkten Pushes auf main

## Toolchain

### Python QA
- ruff (Lint + Importordnung)
- black (Formatierung)
- mypy (Typpruefung)
- pytest
- pytest-cov

### Home Assistant spezifisch
- hassfest (Manifest/Integrationsstruktur)
- Home Assistant test harness fuer Config Flow / Coordinator Tests

### HACS spezifisch
- hacs/action fuer Repository-Validierung
- hacs.json als Metadatenquelle
- Release-Artefakte und Tags konsistent

### Optional empfohlen
- pre-commit Hooks lokal
- CodeQL/SAST
- Dependabot

## Pipeline-Design (GitHub Actions)

### Workflow 1: ci.yml (bei Push/PR)

Jobs:

1. validate-structure
- Checkout
- Python Setup
- Install dev dependencies
- Validiere Dateistruktur custom_components

2. lint
- ruff check
- black --check

3. typecheck
- mypy auf custom_components/siemens_logo

4. hassfest
- Home Assistant hassfest laufen lassen

5. tests
- pytest mit Coverage
- Coverage XML + HTML erzeugen

6. coverage-gate
- Fail bei Coverage < Zielwerte
- Modul-spezifische Gates pruefen

7. hacs-validate
- hacs/action ausfuehren
- Fail bei HACS-Inkompatibilitaet

8. artifact-upload
- Testreports, Coverage-Berichte als Artefakte hochladen

### Workflow 2: release.yml (bei Tag v*.*.*)

Jobs:

1. pre-release-verification
- Wiederhole kritische Checks (lint, tests, hacs-validate, hassfest)

2. package
- Erzeuge sauberes Release-Bundle
- Pruefe Versionskonsistenz manifest/hacs.json/tag

3. publish
- GitHub Release erstellen
- Release Notes aus Changelog

4. post-release-smoke
- Basisinstallation in clean environment simulieren

### Workflow 3: nightly.yml (taeglich)

Jobs:
- Regressionstests
- Optional gegen aktuelle Home Assistant Dev/Beta testen
- Fruehwarnung fuer Breaking Changes

## Teststrategie (hoch)

### Testebenen

1. Unit Tests
- Parser fuer LOGO-Import
- Mapping-Validator
- Adressmodell-Konverter
- Entitaetsfabriken

2. Component Tests
- Coordinator Polling inklusive Fehlerpfade
- Reconnect-Logik
- Schreibschutz-Logik

3. Config/Options Flow Tests
- Erfolgsfall
- Invalid JSON/CSV
- Ungueltige Adressen
- Duplikate

4. Integrationsnahe Tests
- Mocked Modbus Antworten
- Entitaetszustand und Updates in HA

### Coverage-Fokus

Kritische Dateien (Ziel >=95%):
- custom_components/siemens_logo/config_flow.py
- custom_components/siemens_logo/coordinator.py
- custom_components/siemens_logo/__init__.py
- zukunftig: parser/importer module

## HACS-Prozess in der Pipeline

Pflichtartefakte und Checks:

1. hacs.json
- Name, Render Readme, Domains, Home Assistant Version etc.

2. Struktur
- custom_components/siemens_logo korrekt

3. SemVer
- Tag, manifest version und changelog konsistent

4. Validierung
- hacs/action muss bei PR und Release gruen sein

5. Installierbarkeit
- Release-Bundle muss direkt als Custom Repository installierbar sein

## Security und Stabilitaet in CI/CD

- Dependency-Updates via Dependabot
- Security-Scanning (CodeQL)
- Optional: pip-audit in Nightly
- Kein Secret im Repo
- GitHub Environments fuer Release-Schutz

## Rollout in Iterationen

### Iteration 1: Pipeline-Fundament
- pyproject/pytest/mypy/ruff/black konfigurieren
- ci.yml mit lint/type/tests
- erste Coverage-Gates auf 80% initial, dann schrittweise 90%

### Iteration 2: HA + HACS Gates
- hassfest integrieren
- hacs/action integrieren
- branch protection aktivieren

### Iteration 3: TDD-Verankerung
- Test-Skeleton fuer alle Kernmodule
- PR-Template mit TDD-Checkliste
- pre-commit lokal

### Iteration 4: Release-Automatisierung
- release.yml
- Versionierungsregeln
- changelog workflow

### Iteration 5: Hardening
- Nightly, Security Scans, Smoke Tests
- Coverage fuer kritische Pfade auf 95%

## Konkrete Abnahmekriterien je Phase

1. CI-Basis
- PR kann ohne gruene Checks nicht gemerged werden

2. TDD-Prozess
- Jede neue Funktion hat Test vor Implementierung (in PR nachweisbar)

3. Coverage
- Global >=90%, kritische Module >=95%

4. HACS
- hacs/action und hassfest in PR und Release gruen

5. Release
- Tagging erstellt reproduzierbares, installierbares Release

## Risiken und Gegenmassnahmen

1. Unbekanntes LOGO-Dateiformat
- Parser in separatem Modul mit Golden-File-Tests
- Fallback auf JSON/CSV Import

2. Flaky Modbus-Tests
- Mock-First Tests, Integrationstests isolieren

3. Zu strenge Gates frueh
- Coverage stufenweise erhoehen

4. HACS-Anforderungen aendern sich
- Nightly HACS Validation beibehalten

## Unmittelbare naechste Schritte (nur Planung abgeschlossen)

1. Plan freigeben
2. Danach Umsetzung strikt in dieser Reihenfolge:
- Projektkonfiguration fuer QA
- CI-Workflow 1 (PR)
- Test-Skeleton (TDD ready)
- HACS-Validierung
- Release-Workflow

## Entscheidungslog

Dieser Plan priorisiert langfristige Stabilitaet ueber Geschwindigkeit und passt zur gewuenschten Strategie:
- oeffentliches GitHub zuerst
- danach HACS
- hohe Testabdeckung
- TDD als Prozessstandard
