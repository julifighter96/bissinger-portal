"""
capture_gui.py
--------------
Template-Aufnahme per Maus-Ziehen über einem Vollbild-Overlay.
Einfach einen Rahmen um den gewünschten Button ziehen – fertig.
"""

import os
import sys
import json
import tkinter as tk
from tkinter import messagebox
import numpy as np
from PIL import ImageGrab, ImageTk

TEMPLATES = [
    ("templates/btn_haken.png",  "Haken-Button  (neuer Auftrag sichtbar)"),
    ("templates/dropdown.png",   "Dropdown       (Zeitauswahl öffnen)"),
    ("templates/option_30.png",  "Option 30 Min  (im Dropdown)"),
    ("templates/btn_ok.png",     "OK-Button"),
    ("templates/btn_ja.png",     "Ja-Button      (Bestätigungs-Dialog)"),
]

SEARCH_REGION_FILE = "search_region.json"

os.makedirs("templates", exist_ok=True)


# ---------------------------------------------------------------------------
# Overlay-Fenster: Vollbild-Screenshot + Zieh-Auswahl
# ---------------------------------------------------------------------------
class SelectionOverlay(tk.Tk):
    def __init__(self, screenshot, label: str):
        super().__init__()
        self.screenshot = screenshot
        self.result = None          # (x1, y1, x2, y2) nach Loslassen

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+0+0")
        self.configure(cursor="crosshair", bg="black")

        self._start = None
        self._rect_id = None

        self.canvas = tk.Canvas(self, highlightthickness=0, bg="black")
        self.canvas.pack(fill="both", expand=True)

        self._photo = ImageTk.PhotoImage(screenshot)
        self.canvas.create_image(0, 0, anchor="nw", image=self._photo)

        # Halbdurchsichtiges Overlay
        self.canvas.create_rectangle(
            0, 0, screenshot.width, screenshot.height,
            fill="black", stipple="gray25", outline=""
        )

        # Anleitung oben mittig
        self.canvas.create_text(
            screenshot.width // 2, 22,
            text=f"Ziehe einen Rahmen um:  {label}    |    ESC = Überspringen",
            fill="yellow", font=("Segoe UI", 13, "bold"), anchor="center"
        )

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",        self._on_drag)
        self.canvas.bind("<ButtonRelease-1>",  self._on_release)
        self.bind("<Escape>", lambda _: self.destroy())

    def _on_press(self, event):
        self._start = (event.x, event.y)
        if self._rect_id:
            self.canvas.delete(self._rect_id)

    def _on_drag(self, event):
        if not self._start:
            return
        if self._rect_id:
            self.canvas.delete(self._rect_id)
        x0, y0 = self._start
        self._rect_id = self.canvas.create_rectangle(
            x0, y0, event.x, event.y,
            outline="red", width=2, dash=(6, 3)
        )

    def _on_release(self, event):
        if not self._start:
            return
        x1, y1 = self._start
        x2, y2 = event.x, event.y
        if abs(x2 - x1) < 4 or abs(y2 - y1) < 4:
            return   # versehentlicher Klick – ignorieren
        self.result = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        self.destroy()


# ---------------------------------------------------------------------------
# Vorschau-Fenster: zeigt den Ausschnitt + Speichern / Wiederholen
# ---------------------------------------------------------------------------
class PreviewWindow(tk.Tk):
    def __init__(self, region, label: str):
        super().__init__()
        self.confirmed = False

        self.title(f"Vorschau – {label}")
        self.attributes("-topmost", True)
        self.resizable(False, False)

        # Bild anzeigen (min. 80px in jeder Richtung für Lesbarkeit)
        display = region.copy()
        if display.width < 80 or display.height < 80:
            scale = max(80 / display.width, 80 / display.height)
            display = display.resize(
                (int(display.width * scale), int(display.height * scale))
            )

        self._photo = ImageTk.PhotoImage(display)
        tk.Label(self, image=self._photo, relief="sunken", bd=1).pack(padx=12, pady=(12, 4))
        tk.Label(self, text=f"Größe: {region.width} × {region.height} px",
                 font=("Segoe UI", 9)).pack()

        frm = tk.Frame(self)
        frm.pack(pady=10)
        tk.Button(frm, text="✓  Speichern", width=13, bg="#4caf50", fg="white",
                  font=("Segoe UI", 10, "bold"),
                  command=self._save).pack(side="left", padx=6)
        tk.Button(frm, text="↺  Wiederholen", width=13, bg="#f44336", fg="white",
                  font=("Segoe UI", 10),
                  command=self.destroy).pack(side="left", padx=6)

        self.bind("<Return>", lambda _: self._save())
        self.bind("<Escape>", lambda _: self.destroy())

    def _save(self):
        self.confirmed = True
        self.destroy()


# ---------------------------------------------------------------------------
# Aufnahme eines einzelnen Templates
# ---------------------------------------------------------------------------
def capture_one(save_path: str, label: str) -> bool:
    while True:
        # Screenshot BEVOR das Overlay erscheint
        screenshot = ImageGrab.grab()

        overlay = SelectionOverlay(screenshot, label)
        overlay.mainloop()

        if overlay.result is None:
            skip = messagebox.askyesno(
                "Überspringen?",
                f"'{label}' wurde nicht markiert.\n\nDieses Template überspringen?"
            )
            return not skip   # False = überspringen, Schleife weiter oben bricht ab

        x1, y1, x2, y2 = overlay.result
        region = screenshot.crop((x1, y1, x2, y2))

        preview = PreviewWindow(region, label)
        preview.mainloop()

        if preview.confirmed:
            region.save(save_path)
            print(f"  ✓  Gespeichert: {save_path}  ({region.width}×{region.height} px)")
            return True

        print("  ↺  Aufnahme wird wiederholt …")


# ---------------------------------------------------------------------------
# Aufnahme des festen Suchbereichs (statt Bild wird nur die Position/Größe
# als JSON gespeichert; bot.py schränkt damit ALLE Button-Suchen in Flow A
# & B auf diesen Bereich ein, statt Vollbild bzw. maus-relativ zu suchen).
# ---------------------------------------------------------------------------
def capture_search_region() -> bool:
    label = "Such-/Modal-Bereich (wird für ALLE Flows verwendet)"
    while True:
        screenshot = ImageGrab.grab()

        overlay = SelectionOverlay(screenshot, label)
        overlay.mainloop()

        if overlay.result is None:
            skip = messagebox.askyesno(
                "Überspringen?",
                "Der Suchbereich wurde nicht markiert.\n\nDiesen Schritt überspringen?"
            )
            return not skip

        x1, y1, x2, y2 = overlay.result
        region_img = screenshot.crop((x1, y1, x2, y2))

        preview = PreviewWindow(region_img, label)
        preview.mainloop()

        if preview.confirmed:
            data = {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1}
            with open(SEARCH_REGION_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
            print(f"  ✓  Suchbereich gespeichert: {SEARCH_REGION_FILE}  ({data})")
            return True

        print("  ↺  Aufnahme wird wiederholt …")


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------
def main():
    print()
    print("=" * 55)
    print("  Elba-Bot – Template-Aufnahme (GUI)")
    print("=" * 55)
    print()
    print("  1. Stelle sicher, dass das Portal im Browser")
    print("     sichtbar und vollständig geladen ist.")
    print("  2. Pro Template öffnet sich ein Vollbild-Overlay.")
    print("  3. Ziehe einen Rahmen um den Button.")
    print("  4. Bestätige die Vorschau mit 'Speichern'.")
    print()
    input("  Enter drücken um zu starten …")
    print()

    results = []
    for save_path, label in TEMPLATES:
        print(f"\n► Nächstes Template: {label}")
        try:
            ok = capture_one(save_path, label)
        except Exception as exc:
            print(f"  FEHLER: {exc}")
            ok = False
        results.append((save_path, label, ok))

    print()
    print("=" * 55)
    print("  Ergebnis:")
    print("=" * 55)
    for save_path, label, ok in results:
        status = "OK        " if ok else "ÜBERSPRUNGEN"
        print(f"  [{status}]  {save_path}")
    print()

    print("=" * 55)
    print("  Optional: fester Suchbereich für Flow A & B")
    print("=" * 55)
    print("  Schränkt ALLE Button-Suchen (Dropdown, OK, Ja) auf einen")
    print("  von dir gezogenen Bereich ein, statt den ganzen Bildschirm")
    print("  bzw. den Bereich um die Maus zu durchsuchen. Verhindert,")
    print("  dass versehentlich etwas außerhalb des Dialogs erkannt wird.")
    print("  Ziehe dazu einen Rahmen um den Bereich, in dem der")
    print("  Bestätigungs-Dialog immer erscheint (z.B. Bildschirmmitte).")
    print()
    answer = input("  Jetzt festen Suchbereich ziehen? (j/n): ").strip().lower()
    if answer == "j":
        try:
            region_ok = capture_search_region()
        except Exception as exc:
            print(f"  FEHLER: {exc}")
            region_ok = False
        status = "OK        " if region_ok else "ÜBERSPRUNGEN"
        print(f"  [{status}]  {SEARCH_REGION_FILE}")
    else:
        print(f"  Übersprungen – {SEARCH_REGION_FILE} bleibt unverändert (falls vorhanden).")

    print()
    print("  Du kannst jetzt 'python bot.py' starten.")
    print()
    input("  Enter drücken zum Beenden …")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbgebrochen.")
        sys.exit(0)
