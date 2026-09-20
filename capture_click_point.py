"""
capture_click_point.py
-----------------------
Nimmt eine einzelne Klick-Position auf dem Bildschirm auf und speichert sie
in click_points.json. Wird von bot.py fuer Flow B (direkter Ja-Klick ohne
Dropdown) verwendet: dieser Bestaetigungs-Dialog erscheint immer an
derselben Bildschirmposition, daher genuegt ein fest hinterlegter Punkt
statt Bildsuche.

Ablauf:
  1. Portal so oeffnen, dass der "Wollen Sie den Fall wirklich annehmen?"-
     Dialog mit dem Ja-Button sichtbar ist (z.B. Flow B ohne Dropdown).
  2. Dieses Skript starten, Enter druecken.
  3. Genau auf den Ja-Button klicken.
  4. Position wird in click_points.json unter "btn_ja_b" gespeichert.
"""

import json
import sys
import tkinter as tk
from PIL import ImageGrab, ImageTk

CLICK_POINTS_FILE = "click_points.json"
KEY = "btn_ja_b"
LABEL = "Ja-Button (Flow B, ohne Dropdown)"


class ClickOverlay(tk.Tk):
    def __init__(self, screenshot, label):
        super().__init__()
        self.result = None

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+0+0")
        self.configure(cursor="crosshair")

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._photo = ImageTk.PhotoImage(screenshot)
        self.canvas.create_image(0, 0, anchor="nw", image=self._photo)
        self.canvas.create_rectangle(
            0, 0, screenshot.width, screenshot.height,
            fill="black", stipple="gray25", outline=""
        )
        self.canvas.create_text(
            screenshot.width // 2, 22,
            text=f"Klicke genau auf die Stelle fuer:  {label}    |    ESC = Abbrechen",
            fill="yellow", font=("Segoe UI", 13, "bold"), anchor="center"
        )

        self.canvas.bind("<ButtonPress-1>", self._on_click)
        self.bind("<Escape>", lambda _: self.destroy())

    def _on_click(self, event):
        self.result = (event.x, event.y)
        self.destroy()


def main():
    print()
    print("=" * 55)
    print("  Elba-Bot - Klick-Position aufnehmen (Flow B / Ja-Button)")
    print("=" * 55)
    print()
    print(f"  Es wird die Klick-Position fuer '{LABEL}' aufgenommen.")
    print("  Stelle sicher, dass der Bestaetigungs-Dialog (Ja/Nein)")
    print("  JETZT auf dem Bildschirm sichtbar ist, bevor du Enter drueckst.")
    print()
    input("  Enter druecken, sobald der Dialog sichtbar ist ...")

    screenshot = ImageGrab.grab()
    overlay = ClickOverlay(screenshot, LABEL)
    overlay.mainloop()

    if overlay.result is None:
        print("\n  Abgebrochen - nichts gespeichert.")
        input("\n  Enter druecken zum Beenden ...")
        return

    x, y = overlay.result

    try:
        with open(CLICK_POINTS_FILE, "r", encoding="utf-8") as f:
            points = json.load(f)
    except Exception:
        points = {}

    points[KEY] = {"x": x, "y": y}

    with open(CLICK_POINTS_FILE, "w", encoding="utf-8") as f:
        json.dump(points, f, indent=2, ensure_ascii=False)

    print(f"\n  Position gespeichert: x={x}, y={y}")
    print(f"  Gespeichert in: {CLICK_POINTS_FILE}")
    print()
    print("  bot.py verwendet diese Position jetzt automatisch fuer Flow B.")
    print()
    input("  Enter druecken zum Beenden ...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbgebrochen.")
        sys.exit(0)
