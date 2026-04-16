import time
import logging
import numpy as np
import cv2
import pyautogui
from PIL import ImageGrab

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
TEMPLATE_HAKEN     = "templates/btn_haken.png"
TEMPLATE_DROPDOWN  = "templates/dropdown.png"
TEMPLATE_OPTION_30 = "templates/option_30.png"
TEMPLATE_BTN_OK    = "templates/btn_ok.png"
TEMPLATE_BTN_JA    = "templates/btn_ja.png"

CONFIDENCE_THRESHOLD = 0.85
POLL_INTERVAL_MS     = 300
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
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("elba-bot")


# ---------------------------------------------------------------------------
# Template Matching
# ---------------------------------------------------------------------------
def find_button(template_path: str, confidence: float):
    """
    Sucht ein Template auf dem aktuellen Bildschirm.
    Gibt (center_x, center_y) zurück oder None.
    """
    screenshot = np.array(ImageGrab.grab())
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(f"Template nicht gefunden: {template_path}")

    h, w = template.shape
    result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= confidence:
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return (center_x, center_y)
    return None


# ---------------------------------------------------------------------------
# Hilfsfunktion: Warte bis Template sichtbar ist
# ---------------------------------------------------------------------------
def wait_and_click(template_path: str, step_name: str) -> bool:
    """
    Wartet bis zu STEP_TIMEOUT_SEC, bis das Template gefunden wird,
    und klickt dann darauf.
    Gibt True bei Erfolg zurück, False bei Timeout.
    """
    deadline = time.time() + STEP_TIMEOUT_SEC
    interval = POLL_INTERVAL_MS / 1000.0

    while time.time() < deadline:
        try:
            pos = find_button(template_path, CONFIDENCE_THRESHOLD)
        except FileNotFoundError as exc:
            log.error("Template-Datei fehlt: %s", exc)
            return False

        if pos:
            log.info("[%s] gefunden bei %s – klicke.", step_name, pos)
            pyautogui.click(pos[0], pos[1])
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
            pos = find_button(TEMPLATE_HAKEN, CONFIDENCE_THRESHOLD)
        except FileNotFoundError as exc:
            log.error("Template-Datei fehlt: %s", exc)
            time.sleep(2)
            return

        if pos:
            log.info("Schritt 1: btn_haken gefunden bei %s – klicke.", pos)
            pyautogui.click(pos[0], pos[1])
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
    time.sleep(0.8)

    # ------------------------------------------------------------------
    # Schritt 3: Dropdown öffnen
    # ------------------------------------------------------------------
    if not wait_and_click(TEMPLATE_DROPDOWN, "dropdown"):
        return

    # ------------------------------------------------------------------
    # Schritt 4: Warten auf Dropdown-Animation
    # ------------------------------------------------------------------
    time.sleep(0.4)

    # ------------------------------------------------------------------
    # Schritt 5: Option "30 Minuten" wählen
    # ------------------------------------------------------------------
    if not wait_and_click(TEMPLATE_OPTION_30, "option_30"):
        return

    # ------------------------------------------------------------------
    # Schritt 6: Warten
    # ------------------------------------------------------------------
    time.sleep(0.4)

    # ------------------------------------------------------------------
    # Schritt 7: OK klicken
    # ------------------------------------------------------------------
    if not wait_and_click(TEMPLATE_BTN_OK, "btn_ok"):
        return

    # ------------------------------------------------------------------
    # Schritt 8: Warten auf Bestätigungs-Dialog
    # ------------------------------------------------------------------
    time.sleep(0.8)

    # ------------------------------------------------------------------
    # Schritt 9: Ja klicken
    # ------------------------------------------------------------------
    if not wait_and_click(TEMPLATE_BTN_JA, "btn_ja"):
        return

    # ------------------------------------------------------------------
    # Schritt 10: Erfolg
    # ------------------------------------------------------------------
    log.info("Auftrag erfolgreich angenommen ✅")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_bot()
