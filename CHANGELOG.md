# Changelog

Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).
Versionsnummern folgen [Semantic Versioning](https://semver.org/lang/de/).

---

## [Unreleased]

### Added
- LOGO! 8 Standard-Layout (32 vorkonfigurierte I/Os: I1-I8, Q1-Q8, AI1-AI8, AQ1-AQ2, M1-M8)
- Datei-Import: Points-JSON aus HA-Config-Verzeichnis laden
- Multi-Step Options-Flow (Quelle wählen → Konfigurieren)
- GitHub Actions CI/CD Pipeline (lint, typecheck, hassfest, tests, coverage-gate, hacs-validate)
- Release-Workflow mit Pre-Release-Unterstützung

---

## [0.1.0] – 2026-08-11

### Added
- Initiales MVP: Config Flow, Options Flow (JSON-Textarea)
- Entitäten: `switch` (coil), `binary_sensor` (coil/discrete), `sensor` (holding/input)
- Coordinator mit Modbus TCP via pymodbus 3.8.3
- `SiemensLogoCoordinator` mit Reconnect-Logik
- HACS-Metadaten (`hacs.json`, `manifest.json`)

---

<!-- Verlinkungen -->
[Unreleased]: https://github.com/phismith91/ha-siemens-logo/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/phismith91/ha-siemens-logo/releases/tag/v0.1.0
