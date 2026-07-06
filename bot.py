import sys
import os
import time
import json
import logging
import threading
import urllib.request
import numpy as np
import cv2
import pyautogui
from PIL import ImageGrab


def _resource(rel_path: str) -> str:
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel_path)

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
TEMPLATE_HAKEN     = _resource("templates/btn_haken.png")
TEMPLATE_DROPDOWN  = _resource("templates/dropdown.png")
TEMPLATE_OPTION_30 = _resource("templates/option_30.png")
TEMPLATE_BTN_OK    = _resource("templates/btn_ok.png")
TEMPLATE_BTN_JA    = _resource("templates/btn_ja.png")

CONFIDENCE_THRESHOLD = 0.55   # globaler Fallback

# Confidence pro Schritt (überschreibt den globalen Wert)
CONFIDENCE_HAKEN      = 0.7
CONFIDENCE_DROPDOWN   = 0.70
CONFIDENCE_OPTION_30  = 0.70
CONFIDENCE_BTN_OK     = 0.6
CONFIDENCE_BTN_JA     = 0.6

MOUSE_SEARCH_RADIUS  = 200   # px um die Maus herum für OK/Ja-Suche
JA_SEARCH_RADIUS      = 400   # px um die Bildschirmmitte herum für die Ja-Suche (Flow A & B)
CLICK_DELAY_SEC      = 0.4   # Pause zwischen Mausbewegung und Klick

POLL_INTERVAL_MS     = 500
STEP_TIMEOUT_SEC     = 5
PAGE_RELOAD_SEC      = 30   # F5 drücken wenn nach X Sekunden kein Auftrag sichtbar

# ---------------------------------------------------------------------------
# Heartbeat-Monitoring via ntfy.sh
# ---------------------------------------------------------------------------
# Topic selbst wählen – je zufälliger, desto besser (kein Passwortschutz).
# Handy-App: https://ntfy.sh  → Topic abonnieren, fertig.
NTFY_TOPIC           = "elba-bot-karlsruhe-x7k9m2"
NTFY_HEARTBEAT_SEC   = 30 * 60   # alle 30 Minuten "Bot läuft"-Ping

# ---------------------------------------------------------------------------
# Fern-Neustart via ntfy.sh + Hang-Erkennung
# ---------------------------------------------------------------------------
# Neustart von außerhalb auslösen (z.B. vom Handy aus der ntfy-App):
#   curl -d "restart" https://ntfy.sh/elba-bot-karlsruhe-x7k9m2-cmd
# Der Bot beendet sich daraufhin selbst; ein äußerer Loop (siehe
# run_bot_loop.ps1) startet ihn automatisch neu.
NTFY_CMD_TOPIC       = NTFY_TOPIC + "-cmd"
CMD_POLL_SEC         = 10        # wie oft der Kommando-Topic abgefragt wird
HANG_TIMEOUT_SEC     = 3 * 60    # keine Aktivität für X Sekunden = Bot gilt als hängend
HANG_CHECK_SEC       = 15        # wie oft der Watchdog die Aktivität prüft

# ---------------------------------------------------------------------------
# Screenshot-Monitoring
# ---------------------------------------------------------------------------
SCREENSHOT_INTERVAL_SEC = 5 * 60          # alle 5 Minuten
SCREENSHOT_DIR          = _resource("screenshots")
SCREENSHOT_KEEP         = 24              # nur die letzten 24 behalten (~2h)

# ---------------------------------------------------------------------------
# Sicherheit
# ---------------------------------------------------------------------------
pyautogui.FAILSAFE = True


# ---------------------------------------------------------------------------
# ntfy.sh Benachrichtigungen
# ---------------------------------------------------------------------------
def _ntfy(message: str, title: str = "Elba-Bot", priority: str = "default", tags: str = "robot"):
    """Sendet eine Push-Notification via ntfy.sh. Fehler werden nur geloggt."""
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": priority,
                "Tags": tags,
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as exc:
        log.warning("ntfy.sh nicht erreichbar: %s", exc)


def _heartbeat_loop():
    """Läuft im Hintergrund und sendet alle NTFY_HEARTBEAT_SEC einen Lebenszeichen-Ping."""
    while True:
        time.sleep(NTFY_HEARTBEAT_SEC)
        _ntfy("Bot läuft problemlos.", title="Elba-Bot Pforzheim Heartbeat", tags="white_check_mark")


# ---------------------------------------------------------------------------
# Fern-Neustart & Hang-Erkennung
# ---------------------------------------------------------------------------
_last_activity_lock = threading.Lock()
_last_activity = time.time()


def _touch():
    """Markiert, dass die Haupt-Schleife noch aktiv ist (für den Hang-Watchdog)."""
    global _last_activity
    with _last_activity_lock:
        _last_activity = time.time()


def _hang_watchdog_loop():
    """Erzwingt einen Neustart, wenn die Haupt-Schleife zu lange keine Aktivität zeigt."""
    while True:
        time.sleep(HANG_CHECK_SEC)
        with _last_activity_lock:
            age = time.time() - _last_activity
        if age > HANG_TIMEOUT_SEC:
            log.critical("Keine Aktivität seit %.0fs – Bot hängt vermutlich. Erzwinge Neustart.", age)
            _ntfy_screenshot_now()
            _ntfy(f"Bot hängt (keine Aktivität seit {int(age)}s) – erzwinge Neustart.",
                  title="Elba-Bot Pforzheim: Auto-Neustart", priority="high", tags="warning,repeat")
            os._exit(1)


def _cmd_listener_loop():
    """Fragt den ntfy-Kommando-Topic ab und beendet den Bot bei 'restart'."""
    since = int(time.time())
    while True:
        try:
            url = f"https://ntfy.sh/{NTFY_CMD_TOPIC}/json?poll=1&since={since}"
            with urllib.request.urlopen(url, timeout=15) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except ValueError:
                        continue
                    if data.get("event") != "message":
                        continue
                    since = max(since, int(data.get("time", since)) + 1)
                    msg = (data.get("message") or "").strip().lower()
                    if msg == "restart":
                        log.critical("Neustart-Befehl per ntfy empfangen.")
                        _ntfy("Neustart-Befehl empfangen – Bot wird jetzt beendet.",
                              title="Elba-Bot Pforzheim: Manueller Neustart",
                              priority="high", tags="arrows_counterclockwise")
                        time.sleep(1)
                        os._exit(0)
        except Exception as exc:
            log.warning("ntfy Kommando-Listener nicht erreichbar: %s", exc)
        time.sleep(CMD_POLL_SEC)


def _ntfy_screenshot_now():
    """Macht einen Screenshot und schickt ihn sofort als Anhang via ntfy.sh."""
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        ts = time.strftime("%Y-%m-%d_%H-%M-%S")
        path = os.path.join(SCREENSHOT_DIR, f"screen_{ts}.png")
        ImageGrab.grab().save(path)
        with open(path, "rb") as f:
            img_data = f.read()
        req = urllib.request.Request(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=img_data,
            headers={
                "Title": "Elba-Bot Pforzheim: Screenshot bei Fehler",
                "Filename": os.path.basename(path),
                "Tags": "camera,warning",
                "Priority": "high",
            },
            method="PUT",
        )
        urllib.request.urlopen(req, timeout=30)
    except Exception as exc:
        log.warning("Screenshot-Versand fehlgeschlagen: %s", exc)


def _screenshot_loop():
    """Macht alle SCREENSHOT_INTERVAL_SEC einen Screenshot und behält nur die letzten SCREENSHOT_KEEP."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    while True:
        try:
            ts = time.strftime("%Y-%m-%d_%H-%M-%S")
            path = os.path.join(SCREENSHOT_DIR, f"screen_{ts}.png")
            ImageGrab.grab().save(path)
            log.debug("Screenshot: %s", path)
            # Alte Screenshots aufräumen
            files = sorted(
                f for f in os.listdir(SCREENSHOT_DIR)
                if f.startswith("screen_") and f.endswith(".png")
            )
            for old in files[:-SCREENSHOT_KEEP]:
                os.remove(os.path.join(SCREENSHOT_DIR, old))
        except Exception as exc:
            log.warning("Screenshot fehlgeschlagen: %s", exc)
        time.sleep(SCREENSHOT_INTERVAL_SEC)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("elba-bot")


# ---------------------------------------------------------------------------
# Template Matching
# ---------------------------------------------------------------------------
def find_button(template_path: str, confidence: float, region=None):
    """
    Sucht ein Template auf dem aktuellen Bildschirm.
    region = (x, y, breite, hoehe) schränkt den Suchbereich ein.
    Gibt immer das beste Match zurück, sofern es >= confidence ist.
    """
    screenshot = np.array(ImageGrab.grab())
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

    if region is not None:
        rx, ry, rw, rh = region
        search_area = screenshot_gray[ry:ry+rh, rx:rx+rw]
    else:
        rx, ry = 0, 0
        search_area = screenshot_gray

    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(f"Template nicht gefunden: {template_path}")

    h, w = template.shape
    result = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    log.debug("  match '%s': %.3f (threshold %.2f)", template_path, max_val, confidence)
    if max_val >= confidence:
        center_x = rx + max_loc[0] + w // 2
        center_y = ry + max_loc[1] + h // 2
        return (center_x, center_y)
    return None


# ---------------------------------------------------------------------------
# Suchregion um aktuelle Mausposition
# ---------------------------------------------------------------------------
def mouse_region(radius: int = MOUSE_SEARCH_RADIUS):
    sw, sh = pyautogui.size()
    mx, my = pyautogui.position()
    x = max(0, mx - radius)
    y = max(0, my - radius)
    w = min(sw, mx + radius) - x
    h = min(sh, my + radius) - y
    return (x, y, w, h)


# ---------------------------------------------------------------------------
# Hilfsfunktion: Warte bis Template sichtbar ist
# ---------------------------------------------------------------------------
def wait_and_click(template_path: str, step_name: str, confidence: float = CONFIDENCE_THRESHOLD, region=None) -> bool:
    """
    Wartet bis zu STEP_TIMEOUT_SEC, bis das Template gefunden wird,
    und klickt dann darauf.
    Gibt True bei Erfolg zurück, False bei Timeout.
    """
    deadline = time.time() + STEP_TIMEOUT_SEC
    interval = POLL_INTERVAL_MS / 1000.0

    while time.time() < deadline:
        _touch()
        try:
            pos = find_button(template_path, confidence, region)
        except FileNotFoundError as exc:
            log.error("Template-Datei fehlt: %s", exc)
            return False

        if pos:
            log.info("[%s] gefunden bei %s – bewege Maus.", step_name, pos)
            pyautogui.moveTo(pos[0], pos[1], duration=0.3)
            time.sleep(CLICK_DELAY_SEC)
            pyautogui.click()
            return True

        time.sleep(interval)

    log.warning("[%s] Timeout nach %ds – Button nicht gefunden.", step_name, STEP_TIMEOUT_SEC)
    return False


# ---------------------------------------------------------------------------
# Haupt-Bot-Loop
# ---------------------------------------------------------------------------
def run_bot():
    log.info("Elba-Bot gestartet. Notbremse: Maus in obere linke Ecke.")
    _ntfy("Elba-Bot wurde gestartet.", title="Elba-Bot Pforzheim gestartet", priority="low", tags="green_circle")

    heartbeat = threading.Thread(target=_heartbeat_loop, daemon=True)
    heartbeat.start()

    screenshotter = threading.Thread(target=_screenshot_loop, daemon=True)
    screenshotter.start()

    watchdog = threading.Thread(target=_hang_watchdog_loop, daemon=True)
    watchdog.start()

    cmd_listener = threading.Thread(target=_cmd_listener_loop, daemon=True)
    cmd_listener.start()

    try:
        while True:
            try:
                _touch()
                _process_one_order()
            except pyautogui.FailSafeException:
                log.critical("Failsafe ausgelöst – Bot wird beendet.")
                _ntfy_screenshot_now()
                _ntfy("Failsafe ausgelöst! Bot wurde manuell gestoppt (Maus in Ecke).",
                      title="Elba-Bot Pforzheim gestoppt", priority="high", tags="stop_sign")
                raise
            except Exception as exc:
                log.error("Unerwarteter Fehler: %s – starte Schritt 1 neu.", exc)
                time.sleep(1)
    except pyautogui.FailSafeException:
        raise
    except Exception as exc:
        _ntfy_screenshot_now()
        _ntfy(f"Bot abgestürzt!\n{type(exc).__name__}: {exc}",
              title="Elba-Bot Pforzheim CRASH", priority="urgent", tags="rotating_light")
        log.critical("Fataler Fehler: %s", exc)
        raise


def _flow_dropdown_ok_ja() -> bool:
    """Flow A: Dropdown → 30 Min → OK → Ja"""
    # Schritt 3: Dropdown klicken
    if not wait_and_click(TEMPLATE_DROPDOWN, "dropdown", CONFIDENCE_DROPDOWN):
        return False

    time.sleep(1.0)

    # Schritt 5: Option "30 Minuten" per Tastatur wählen
    pyautogui.press('home')
    time.sleep(0.3)
    pyautogui.press('down', presses=5, interval=0.15)
    time.sleep(0.3)
    pyautogui.press('enter')
    log.info("Flow A: Dropdown auf '30 Minuten' gesetzt.")

    time.sleep(1.0)

    # Schritt 7: OK klicken
    if not wait_and_click(TEMPLATE_BTN_OK, "btn_ok", CONFIDENCE_BTN_OK, mouse_region()):
        return False

    # Maus zur Bildschirmmitte
    sw, sh = pyautogui.size()
    pyautogui.moveTo(sw // 2, sh // 2, duration=0.4)
    time.sleep(1.5)

    # Ja klicken
    if not wait_and_click(TEMPLATE_BTN_JA, "btn_ja", CONFIDENCE_BTN_JA, mouse_region(JA_SEARCH_RADIUS)):
        return False

    log.info("Flow A abgeschlossen ✅")
    return True


def _flow_direkt_ja() -> bool:
    """Flow B: direkt Ja klicken (kein Dropdown)"""
    # Genau wie Flow A: zur Bildschirmmitte, dann im Bereich von JA_SEARCH_RADIUS suchen.
    sw, sh = pyautogui.size()
    pyautogui.moveTo(sw // 2, sh // 2, duration=0.4)
    time.sleep(1.5)

    if not wait_and_click(TEMPLATE_BTN_JA, "btn_ja", CONFIDENCE_BTN_JA, mouse_region(JA_SEARCH_RADIUS)):
        return False

    log.info("Flow B abgeschlossen ✅")
    return True


def _process_one_order():
    """
    Vollständiger Ablauf für einen Auftrag.
    Nach dem Haken-Klick wird automatisch erkannt, welcher Flow greift:
      Flow A: Dropdown sichtbar → Dropdown → OK → Ja
      Flow B: kein Dropdown → direkt Ja
    """
    interval = POLL_INTERVAL_MS / 1000.0

    # ------------------------------------------------------------------
    # Schritt 1: Haken-Button (neuer Auftrag sichtbar)
    # Nach PAGE_RELOAD_SEC ohne Fund → F5 drücken und weiter suchen
    # ------------------------------------------------------------------
    log.debug("Schritt 1: Suche btn_haken …")
    last_reload = time.time()
    while True:
        _touch()
        try:
            pos = find_button(TEMPLATE_HAKEN, CONFIDENCE_HAKEN)
        except FileNotFoundError as exc:
            log.error("Template-Datei fehlt: %s", exc)
            time.sleep(2)
            return

        if pos:
            log.info("Schritt 1: btn_haken gefunden bei %s – bewege Maus.", pos)
            _ntfy("Neuer Auftrag erkannt – starte Bearbeitung.",
                  title="Elba-Bot Pforzheim: Auftrag erkannt", priority="default", tags="bell")
            pyautogui.moveTo(pos[0], pos[1], duration=0.3)
            time.sleep(CLICK_DELAY_SEC)
            pyautogui.click()
            break

        if time.time() - last_reload >= PAGE_RELOAD_SEC:
            log.info("Kein Auftrag seit %ds – drücke F5 (Seite neu laden).", PAGE_RELOAD_SEC)
            pyautogui.hotkey('f5')
            time.sleep(1.5)
            last_reload = time.time()

        time.sleep(interval)

    # ------------------------------------------------------------------
    # Schritt 2: Warten auf Modal-Animation, dann Flow erkennen
    # Mehrere Versuche über DROPDOWN_DETECT_SEC Sekunden, damit eine
    # langsame Modal-Animation nicht fälschlich zu Flow B führt.
    # ------------------------------------------------------------------
    DROPDOWN_DETECT_SEC = 4.0   # wie lange maximal auf Dropdown warten
    DROPDOWN_POLL_SEC   = 0.4   # Abstand zwischen den Versuchen

    time.sleep(1.5)             # Basis-Wartezeit für Modal-Öffnung

    dropdown_pos = None
    deadline = time.time() + DROPDOWN_DETECT_SEC
    attempt = 0
    while time.time() < deadline:
        _touch()
        attempt += 1
        dropdown_pos = find_button(TEMPLATE_DROPDOWN, CONFIDENCE_DROPDOWN)
        if dropdown_pos:
            log.info("Flow A erkannt (Dropdown nach %d Versuch(en) sichtbar).", attempt)
            break
        log.debug("Dropdown-Suche Versuch %d – noch nicht sichtbar.", attempt)
        time.sleep(DROPDOWN_POLL_SEC)

    if dropdown_pos:
        success = _flow_dropdown_ok_ja()
    else:
        log.info("Flow B erkannt (Dropdown nach %d Versuch(en) nicht gefunden).", attempt)
        success = _flow_direkt_ja()

    if success:
        # Warten bis der Haken-Button verschwindet, bevor die nächste Suche startet.
        # Verhindert Doppelerkennung ohne Seiten-Reload.
        deadline = time.time() + 10.0
        while time.time() < deadline:
            _touch()
            if find_button(TEMPLATE_HAKEN, CONFIDENCE_HAKEN) is None:
                break
            time.sleep(0.5)
        else:
            # Deadline überschritten – Haken noch sichtbar → Flow hat nicht funktioniert
            log.warning("Haken noch sichtbar nach 10s – Auftrag wurde NICHT abgeschlossen.")
            _ntfy_screenshot_now()
            _ntfy("Haken noch sichtbar nach vermeintlichem Abschluss – bitte prüfen!",
                  title="Elba-Bot Pforzheim: Fehler", priority="high", tags="warning")
            time.sleep(5.0)
            return
        _ntfy("Auftrag erfolgreich abgeschlossen ✅",
              title="Elba-Bot Pforzheim: Auftrag erledigt", priority="low", tags="white_check_mark,tada")
        time.sleep(1.0)
    else:
        _ntfy_screenshot_now()
        _ntfy("Auftrag konnte nicht abgeschlossen werden – bitte prüfen!",
              title="Elba-Bot Pforzheim: Fehler", priority="high", tags="warning")
        time.sleep(2.0)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_bot()
