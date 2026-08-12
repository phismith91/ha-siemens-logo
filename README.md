# Siemens LOGO! – Home Assistant Integration

[![CI](https://github.com/phismith91/ha-siemens-logo/actions/workflows/ci.yml/badge.svg)](https://github.com/phismith91/ha-siemens-logo/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/phismith91/ha-siemens-logo?label=stable)](https://github.com/phismith91/ha-siemens-logo/releases/latest)
[![Pre-release](https://img.shields.io/github/v/release/phismith91/ha-siemens-logo?include_prereleases&label=pre-release)](https://github.com/phismith91/ha-siemens-logo/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-%3E%3D2025.1-blue)](https://www.home-assistant.io)
[![License](https://img.shields.io/github/license/phismith91/ha-siemens-logo)](LICENSE)

Home Assistant Custom Integration für die **Siemens LOGO! 8 (0BA8)** SPS über Modbus TCP.

---

## Enthaltene Features

| Feature | Beschreibung |
|---|---|
| Config Flow | Verbindung über HA UI (Host, Port, Unit-ID) |
| LOGO! 8 Standard-Layout | Ein Klick – alle I/Os sofort in HA (I1-I8, Q1-Q8, AI1-AI8, AQ1-AQ2, M1-M8) |
| Datei-Import | Points-JSON aus HA-Config-Verzeichnis laden |
| Manuelles JSON | Eigene Konfiguration direkt eintippen |
| Entitäten | `switch` (coil), `binary_sensor` (coil/discrete), `sensor` (holding/input) |
| Scan-Intervall | Konfigurierbar über Integrationsoptionen |

---

## Installation

### Via HACS (empfohlen)

1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL: `https://github.com/phismith91/ha-siemens-logo` | Kategorie: `Integration`
3. Siemens LOGO suchen und installieren
4. Home Assistant neu starten

### Manuell

```bash
cp -r custom_components/siemens_logo <ha-config>/custom_components/siemens_logo
```

Danach HA neu starten.

---

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → "Siemens LOGO"**
2. Host/IP, Port (Standard: `502`), Unit-ID (Standard: `1`) eintragen

### Optionen (nach der Einrichtung)

In den Integrationsoptionen Konfigurationsquelle wählen:

| Quelle | Beschreibung |
|---|---|
| **LOGO! 8 Standard-Layout** | Alle 32 Standard-I/Os sofort aktiv – empfohlen für den Start |
| **Aus Datei laden** | JSON-Datei im HA-Config-Verzeichnis angeben (z. B. `siemens_logo_points.json`) |
| **Manuell** | Points-JSON direkt im Textfeld eingeben |

---

## Datei-Import (Kundenworkflow)

1. JSON-Datei (z. B. `meine_logo.json`) über den HA File Editor nach `/config/` hochladen
2. Integrationsoptionen öffnen → **„Aus Datei laden"**
3. Dateipfad angeben: `meine_logo.json`
4. Speichern → Entities werden automatisch angelegt

**Beispiel-Datei** (`logo_points.example.json` im Repo):

```json
[
  { "key": "q1", "name": "Pumpe 1", "platform": "switch", "kind": "coil", "address": 8192 },
  { "key": "i1", "name": "Druckschalter", "platform": "binary_sensor", "kind": "discrete", "address": 1 },
  { "key": "ai1", "name": "Temperatur", "platform": "sensor", "kind": "holding", "address": 0,
    "scale": 0.1, "precision": 1, "unit_of_measurement": "°C", "device_class": "temperature" }
]
```

### Point-JSON Schema

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `key` | ✓ | Eindeutiger Schlüssel |
| `name` | ✓ | Anzeigename in HA |
| `platform` | ✓ | `sensor` \| `switch` \| `binary_sensor` |
| `kind` | ✓ | `coil` \| `discrete` \| `holding` \| `input` |
| `address` | ✓ | Modbus-Register-Adresse |
| `scale` | – | Skalierungsfaktor (Standard: `1.0`) |
| `precision` | – | Nachkommastellen |
| `unit_of_measurement` | – | z. B. `"°C"`, `"V"`, `"bar"` |
| `device_class` | – | z. B. `"temperature"`, `"voltage"` |

---

## LOGO! 8 Modbus-Adresstabelle (Standard 0BA8)

| Typ | LOGO! Bezeichnung | Modbus-Art | Adressbereich |
|---|---|---|---|
| Digitale Eingänge | I1–I8 | Discrete Input | 1–8 |
| Digitale Ausgänge | Q1–Q8 | Coil | 8192–8199 |
| Analoge Eingänge | AI1–AI8 | Holding Register | 0–7 |
| Analoge Ausgänge | AQ1–AQ2 | Holding Register | 528–529 |
| Merker | M1–M8 | Coil | 8256–8263 |

---

## Entwicklung

Siehe [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) für den vollständigen Entwicklungsplan.

```bash
# Virtuelle Umgebung anlegen (Python 3.12)
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate        # Linux/macOS

# Dev-Abhängigkeiten installieren
pip install -r requirements-dev.txt
pip install -e . --no-deps

# Tests lokal
pytest tests/test_tdd_policy.py tests/test_manifest.py -v --no-cov

# Alle Tests (GitHub Actions / Linux)
pytest
```

---

## Release-Prozess

### Stabiles Release (`v1.2.3`)

```bash
# 1. manifest.json version auf "1.2.3" setzen
# 2. CHANGELOG.md aktualisieren
# 3. Commit + Tag
git add custom_components/siemens_logo/manifest.json CHANGELOG.md
git commit -m "chore(release): v1.2.3"
git tag v1.2.3
git push origin master --tags
# → release.yml läuft, GitHub Release wird erstellt (kein Pre-Release-Flag)
```

### Pre-Release (`v1.2.3-beta.1`)

```bash
# 1. manifest.json version auf "1.2.3-beta.1" setzen
# 2. CHANGELOG.md aktualisieren
git add custom_components/siemens_logo/manifest.json CHANGELOG.md
git commit -m "chore(release): v1.2.3-beta.1"
git tag v1.2.3-beta.1
git push origin master --tags
# → release.yml läuft, GitHub Release wird als Pre-Release markiert
```

Erlaubte Tag-Formate: `v1.2.3`, `v1.2.3-alpha.1`, `v1.2.3-beta.1`, `v1.2.3-rc.1`

### Badges aktualisieren

Nach dem ersten Push die drei `OWNER/REPO`-Platzhalter in dieser Datei durch den echten GitHub-Pfad ersetzen:

```bash
# Repo-URL ist bereits gesetzt: phismith91/ha-siemens-logo
# Falls der Repo-Name abweicht:
sed -i 's|phismith91/ha-siemens-logo|DEIN_USER/DEIN_REPO|g' README.md CHANGELOG.md
git add README.md CHANGELOG.md && git commit -m "chore: fix repo URL"
```

---

## Lizenz

MIT – siehe [LICENSE](LICENSE)

