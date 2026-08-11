# Siemens LOGO Custom Integration (MVP)

Dieses Verzeichnis enthaelt ein Home-Assistant-Custom-Component fuer Siemens LOGO ueber Modbus TCP.

## Enthaltene Features

- Config Flow in der HA UI (Host, Port, Unit-ID)
- Optionen in der HA UI:
  - Scan-Intervall
  - Point-Mapping als JSON
- Entitaeten:
  - switch (coil)
  - binary_sensor (coil/discrete)
  - sensor (holding/input)

## Installation

1. Kopiere den Ordner `custom_components/siemens_logo` in deine Home-Assistant-Config.
2. Starte Home Assistant neu.
3. Gehe zu Einstellungen -> Geraete & Dienste -> Integration hinzufuegen.
4. Suche nach "Siemens LOGO".
5. Trage Host/Port/Unit-ID ein.
6. In den Integrationsoptionen Points-JSON aus `logo_points.example.json` eintragen und auf deine LOGO-Register anpassen.

## Point-JSON Schema

Jeder Eintrag braucht mindestens:

- key: eindeutiger Schluessel
- name: Anzeigename
- platform: sensor | switch | binary_sensor
- kind: coil | discrete | holding | input
- address: Register- oder Coil-Adresse

Optional fuer sensor:

- scale (Standard 1.0)
- precision (z. B. 1)
- unit_of_measurement (z. B. "V")
- device_class (z. B. "voltage")

## Wichtige Hinweise

- Das ist ein MVP als Startpunkt, keine fertige Produktintegration.
- Fuer produktiven Betrieb sollten noch dazu:
  - bessere Adressvalidierung
  - Bulk-Reads statt Einzelabfragen
  - Device-Info/Diagnostics
  - Tests (pytest + HA test harness)
