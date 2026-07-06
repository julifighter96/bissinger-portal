# Elba-Bot – Automatische Auftragsannahme

Automatisiert die Annahme von Aufträgen im Portal **Elbaverwaltung**
(`assistance.imhosting.de/elba_orders`) rein auf Bildschirmebene –
ohne Playwright, Selenium oder CDP.

Verwendet: **OpenCV** (Template Matching) + **PyAutoGUI** (Maussteuerung)

---

## Schnellstart

### 1. Abhängigkeiten installieren

```
pip install -r requirements.txt
```

### 2. Chrome öffnen und einloggen

Entweder manuell Chrome starten und das Portal aufrufen, oder:

```
start_chrome_debug.bat
```

Dann im Browser einloggen. Den Browser **offen lassen** – der Bot
arbeitet auf dem sichtbaren Bildschirm.

### 3. Referenzbilder aufnehmen (einmalig)

```
python capture_buttons.py
```

Das Skript führt dich durch die Aufnahme aller 5 Template-Bilder:

| Datei | Was wird aufgenommen |
|---|---|
| `templates/btn_haken.png` | Haken-Button bei neuem Auftrag |
| `templates/dropdown.png` | Dropdown für die Zeitauswahl |
| `templates/option_30.png` | Eintrag „30 Minuten" im Dropdown |
| `templates/btn_ok.png` | OK-Button im Dialog |
| `templates/btn_ja.png` | Ja-Button zur Bestätigung |

**Bedienung pro Bild:**
1. Maus oben-links auf den Button positionieren → `Enter`
2. Maus unten-rechts auf den Button positionieren → `Enter`
3. Vorschau prüfen → `j` zum Speichern oder `n` zum Wiederholen

> Tipp: Nimm die Bilder auf, während das Portal in dem Zustand ist,
> in dem der jeweilige Button sichtbar ist.

### 4. Bot starten

```
python bot.py
```

Der Bot läuft in einer Endlosschleife und scannt alle 300 ms den
Bildschirm. Sobald ein Auftrag erscheint, klickt er automatisch durch
den gesamten Ablauf.

---

## Ablauf im Detail

```
[Scan] btn_haken sichtbar?
  → Klick
  → 800 ms warten (Modal-Animation)
[Scan] dropdown sichtbar?
  → Klick (Dropdown öffnen)
  → 400 ms warten
[Scan] option_30 sichtbar?
  → Klick (30 Minuten wählen)
  → 400 ms warten
[Scan] btn_ok sichtbar?
  → Klick
  → 800 ms warten (Bestätigungs-Dialog)
[Scan] btn_ja sichtbar?
  → Klick
  → Log: Auftrag erfolgreich angenommen ✅
  → zurück zum Anfang
```

Bei Timeout eines Schritts (Standard: 5 s) → Warnung im Log,
Neustart ab Schritt 1.

---

## Konfiguration (`bot.py`)

| Variable | Standard | Beschreibung |
|---|---|---|
| `CONFIDENCE_THRESHOLD` | `0.85` | Mindest-Übereinstimmung beim Template Matching (0–1) |
| `POLL_INTERVAL_MS` | `300` | Scan-Intervall in Millisekunden |
| `STEP_TIMEOUT_SEC` | `5` | Maximale Wartezeit pro Schritt in Sekunden |

---

## Notbremse

**Maus in die obere linke Bildschirmecke bewegen** – PyAutoGUI bricht
sofort ab (`FAILSAFE = True`).

---

## Neustart von außerhalb (Server hängt / Fernwartung)

Der Bot erkennt Hänger selbst und lässt sich zusätzlich manuell per Handy
neu starten – ganz ohne offene Ports oder VPN, über den ohnehin schon
genutzten ntfy.sh-Kanal:

- **Automatisch:** Zeigt die Haupt-Schleife `HANG_TIMEOUT_SEC` (Standard
  3 Minuten) lang keine Aktivität, beendet sich der Bot selbst und
  schickt vorher eine ntfy-Warnung samt Screenshot.
- **Manuell:** Nachricht `restart` an den Kommando-Topic
  `elba-bot-karlsruhe-x7k9m2-cmd` senden, z.B.
  ```
  curl -d "restart" https://ntfy.sh/elba-bot-karlsruhe-x7k9m2-cmd
  ```
  oder direkt aus der ntfy-App heraus (Topic abonnieren/veröffentlichen).

Damit der Prozess nach einem Selbst-Beenden auch wirklich wieder hochkommt,
läuft auf dem Server nicht mehr direkt `ElbaBot.exe`, sondern
[`run_bot_loop.ps1`](run_bot_loop.ps1) im Autostart. Das Skript startet
`dist\ElbaBot.exe` in einer Endlosschleife neu, sobald der Prozess (aus
welchem Grund auch immer) beendet wird.

**Einrichtung auf dem Server:**
1. `ElbaBot.exe` wie gewohnt bauen (liegt danach in `dist\`).
2. Bisherige Autostart-Verknüpfung zu `ElbaBot.exe` entfernen.
3. Neue Verknüpfung im Autostart-Ordner (`shell:startup`) mit folgendem Ziel anlegen:
   ```
   powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "E:\bissinger-portal\run_bot_loop.ps1"
   ```

Restart-Log landet in `run_bot_loop.log` neben dem Skript.

---

## Fehlerbehebung

| Problem | Lösung |
|---|---|
| Button wird nicht erkannt | `CONFIDENCE_THRESHOLD` auf `0.80` senken oder Template neu aufnehmen |
| Klick trifft daneben | Template-Ausschnitt enger wählen (nur Button, kein Rand) |
| „Template nicht gefunden"-Fehler | `capture_buttons.py` erneut ausführen |
| Bot klickt zu schnell | Wartezeiten im Code erhöhen |

---

## Projektstruktur

```
bot.py                  ← Haupt-Bot
capture_buttons.py      ← Einmaliges Aufnehmen der Referenzbilder
requirements.txt        ← Python-Abhängigkeiten
start_chrome_debug.bat  ← Chrome mit Portal öffnen
templates/
  btn_haken.png
  dropdown.png
  option_30.png
  btn_ok.png
  btn_ja.png
```
