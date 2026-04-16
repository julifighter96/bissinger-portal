"""
capture_buttons.py
------------------
Nimmt alle 5 Template-Bilder nacheinander auf.

Bedienung pro Bild:
  1. Maus oben-links auf den Button-Bereich positionieren → Enter drücken
  2. Maus unten-rechts auf den Button-Bereich positionieren → Enter drücken
  3. Ausschnitt wird gespeichert und als Vorschau angezeigt
  4. Mit j/n bestätigen oder wiederholen
"""

import os
import sys
import time
import numpy as np
import cv2
import pyautogui
from PIL import ImageGrab, Image

TEMPLATES = [
    ("templates/btn_haken.png",    "Haken-Button (neuer Auftrag)"),
    ("templates/dropdown.png",     "Dropdown (Zeitauswahl)"),
    ("templates/option_30.png",    "Option '30 Minuten'"),
    ("templates/btn_ok.png",       "OK-Button"),
    ("templates/btn_ja.png",       "Ja-Button (Bestätigung)"),
]

os.makedirs("templates", exist_ok=True)


def grab_region(x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    """Bildschirmausschnitt als numpy-Array (BGR)."""
    img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def wait_for_enter(prompt: str) -> None:
    input(prompt)


def capture_one(save_path: str, description: str) -> None:
    print(f"\n{'='*60}")
    print(f"  Aufnahme: {description}")
    print(f"  Zieldatei: {save_path}")
    print(f"{'='*60}")

    while True:
        print("\nSchritt 1/2: Positioniere die Maus OBEN-LINKS des Buttons.")
        wait_for_enter("  → Enter drücken wenn bereit …")
        x1, y1 = pyautogui.position()
        print(f"  Oben-links erfasst: ({x1}, {y1})")

        print("\nSchritt 2/2: Positioniere die Maus UNTEN-RECHTS des Buttons.")
        wait_for_enter("  → Enter drücken wenn bereit …")
        x2, y2 = pyautogui.position()
        print(f"  Unten-rechts erfasst: ({x2}, {y2})")

        if x2 <= x1 or y2 <= y1:
            print("  FEHLER: Unten-rechts muss größer als oben-links sein. Bitte wiederholen.")
            continue

        # Ausschnitt aufnehmen
        region = grab_region(x1, y1, x2, y2)
        print(f"  Ausschnitt: {region.shape[1]}x{region.shape[0]} px")

        # Vorschau über PIL (Windows-Bildbetrachter)
        region_rgb = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)
        preview = Image.fromarray(region_rgb)
        preview.show()

        answer = input("\n  Bild korrekt? (j = speichern / n = wiederholen): ").strip().lower()

        if answer == "j":
            cv2.imwrite(save_path, region)
            print(f"  Gespeichert: {save_path}")
            break
        else:
            print("  Aufnahme wird wiederholt …")


def main() -> None:
    print("\nElba-Bot – Template-Aufnahme")
    print("Stelle sicher, dass der Browser geöffnet und das Portal sichtbar ist.\n")
    time.sleep(1)

    for save_path, description in TEMPLATES:
        capture_one(save_path, description)

    print("\n\nAlle Templates gespeichert:")
    for save_path, description in TEMPLATES:
        status = "OK" if os.path.exists(save_path) else "FEHLT"
        print(f"  [{status}]  {save_path}  ({description})")

    print("\nDu kannst jetzt 'python bot.py' starten.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbgebrochen.")
        sys.exit(0)
