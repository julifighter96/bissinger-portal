import sys
import os
import time
import logging
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
CONFIDENCE_HAKEN      = 0.75
CONFIDENCE_DROPDOWN   = 0.70
CONFIDENCE_OPTION_30  = 0.70
CONFIDENCE_BTN_OK     = 0.6
CONFIDENCE_BTN_JA     = 0.6

MOUSE_SEARCH_RADIUS  = 200   # px um die Maus herum für OK/Ja-Suche
CLICK_DELAY_SEC      = 0.4   # Pause zwischen Mausbewegung und Klick

POLL_INTERVAL_MS     = 500
STEP_TIMEOUT_SEC     = 5
PAGE_RELOAD_SEC      = 30   # F5 drücken wenn nach X Sekunden kein Auftrag sichtbar

# ---------------------------------------------------------------------------
# Sicherheit
# ---------------------------------------------------------------------------
pyautogui.FAILSAFE = True

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

    while True:
        try:
            _process_one_order()
        except pyautogui.FailSafeException:
            log.critical("Failsafe ausgelöst – Bot wird beendet.")
            raise
        except Exception as exc:
            log.error("Unerwarteter Fehler: %s – starte Schritt 1 neu.", exc)
            time.sleep(1)


def _process_one_order():
    """
    Vollständiger Ablauf für einen Auftrag (Schritte 1–10).
    Bei Fehler in einem Schritt: zurück zu Schritt 1.
    """
    interval = POLL_INTERVAL_MS / 1000.0

    # ------------------------------------------------------------------
    # Schritt 1: Haken-Button (neuer Auftrag sichtbar)
    # Nach PAGE_RELOAD_SEC ohne Fund → F5 drücken und weiter suchen
    # ------------------------------------------------------------------
    log.debug("Schritt 1: Suche btn_haken …")
    last_reload = time.time()
    while True:
        try:
            pos = find_button(TEMPLATE_HAKEN, CONFIDENCE_HAKEN)
        except FileNotFoundError as exc:
            log.error("Template-Datei fehlt: %s", exc)
            time.sleep(2)
            return

        if pos:
            log.info("Schritt 1: btn_haken gefunden bei %s – bewege Maus.", pos)
            pyautogui.moveTo(pos[0], pos[1], duration=0.3)
            time.sleep(CLICK_DELAY_SEC)
            pyautogui.click()
            break

        if time.time() - last_reload >= PAGE_RELOAD_SEC:

            log.info("Kein Auftrag seit %ds – drücke F5 (Seite neu laden).", PAGE_RELOAD_SEC)
            pyautogui.hotkey('f5')
            time.sleep(1.5)   # kurz warten bis Seite geladen ist
            last_reload = time.time()

        time.sleep(interval)

    # ------------------------------------------------------------------
    # Schritt 2: Warten auf Modal-Animation
    # ------------------------------------------------------------------
    time.sleep(1.5)

    # ------------------------------------------------------------------
    # Schritt 3: Dropdown klicken (fokussiert das Select-Element)
    # ------------------------------------------------------------------
    if not wait_and_click(TEMPLATE_DROPDOWN, "dropdown", CONFIDENCE_DROPDOWN):
        return

    # ------------------------------------------------------------------
    # Schritt 4: Warten auf Dropdown-Animation
    # ------------------------------------------------------------------
    time.sleep(1.0)

    # ------------------------------------------------------------------
    # Schritt 5: Option "30 Minuten" per Tastatur wählen
    # Standard ist "5" (Index 0) → 5× Pfeil-unten → "30" (Index 5)
    # ------------------------------------------------------------------
    pyautogui.press('home')
    time.sleep(0.3)
    pyautogui.press('down', presses=5, interval=0.15)
    time.sleep(0.3)
    pyautogui.press('enter')
    log.info("Schritt 5: Dropdown auf '30 Minuten' gesetzt.")

    # ------------------------------------------------------------------
    # Schritt 6: Warten
    # ------------------------------------------------------------------
    time.sleep(1.0)

    # ------------------------------------------------------------------
    # Schritt 7: OK klicken
    # ------------------------------------------------------------------
    if not wait_and_click(TEMPLATE_BTN_OK, "btn_ok", CONFIDENCE_BTN_OK, mouse_region()):
        return

    # ------------------------------------------------------------------
    # Schritt 8: Maus zur Bildschirmmitte (Dialog ist immer zentriert)
    # ------------------------------------------------------------------
    sw, sh = pyautogui.size()
    pyautogui.moveTo(sw // 2, sh // 2, duration=0.4)
    time.sleep(1.5)

    # ------------------------------------------------------------------
    # Schritt 9: Ja klicken
    # ------------------------------------------------------------------
    if not wait_and_click(TEMPLATE_BTN_JA, "btn_ja", CONFIDENCE_BTN_JA, mouse_region()):
        return

    # ------------------------------------------------------------------
    # Schritt 10: Erfolg
    # ------------------------------------------------------------------
    log.info("Auftrag erfolgreich angenommen ✅")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_bot()
