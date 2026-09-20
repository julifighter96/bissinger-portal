"""
capture_gui.py
--------------
Bereichs-Auswahl per Maus-Ziehen über einem Vollbild-Overlay.
Nimmt KEINE Template-Bilder mehr auf (die liegen bereits in templates/),
sondern legt pro Schritt nur einen Suchbereich (x, y, breite, hoehe) fest,
auf den bot.py die jeweilige Bildsuche einschränkt. Einfach einen Rahmen um
die Stelle ziehen, an der der jeweilige Button/Dialog immer erscheint.
"""

import os
import sys
import json
import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab, ImageTk

STEPS = [
    ("haken",    "Haken-Button   (neuer Auftrag sichtbar)"),
    ("dropdown", "Dropdown       (Zeitauswahl öffnen)"),
    ("btn_ok",   "OK-Button"),
    ("btn_ja",   "Ja-Button      (Bestätigung, Flow A mit Dropdown)"),
    ("btn_ja_b", "Ja-Button      (Bestätigung, Flow B ohne Dropdown)"),
]

STEP_REGIONS_FILE = "step_regions.json"


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
            text=f"Ziehe einen Rahmen um den Suchbereich für:  {label}    |    ESC = Überspringen",
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
# Vorschau-Fenster: zeigt den gewählten Bereich + Speichern / Wiederholen
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
        tk.Button(frm, text="✓  Übernehmen", width=13, bg="#4caf50", fg="white",
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
# Aufnahme eines einzelnen Suchbereichs (kein Bild wird gespeichert)
# ---------------------------------------------------------------------------
def capture_step_region(label: str):
    """Lässt einen Bereich ziehen und liefert (x, y, breite, hoehe) zurück,
    oder None, wenn der Schritt übersprungen wurde."""
    while True:
        screenshot = ImageGrab.grab()

        overlay = SelectionOverlay(screenshot, label)
        overlay.mainloop()

        if overlay.result is None:
            skip = messagebox.askyesno(
                "Überspringen?",
                f"Für '{label}' wurde kein Bereich markiert.\n\nDiesen Schritt überspringen?"
            )
            if skip:
                return None
            continue   # nochmal versuchen

        x1, y1, x2, y2 = overlay.result
        region_img = screenshot.crop((x1, y1, x2, y2))

        preview = PreviewWindow(region_img, label)
        preview.mainloop()

        if preview.confirmed:
            return (x1, y1, x2 - x1, y2 - y1)

        print("  ↺  Auswahl wird wiederholt …")


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------
def main():
    print()
    print("=" * 55)
    print("  Elba-Bot – Suchbereiche festlegen")
    print("=" * 55)
    print()
    print("  Die Template-Bilder liegen bereits in templates/ und werden")
    print("  hier NICHT neu aufgenommen. Es wird nur pro Schritt ein")
    print("  Suchbereich gezogen, auf den bot.py die Bildsuche einschränkt.")
    print()
    print("  1. Stelle sicher, dass das Portal im Browser")
    print("     sichtbar und vollständig geladen ist.")
    print("  2. Pro Schritt öffnet sich ein Vollbild-Overlay.")
    print("  3. Ziehe einen Rahmen um den Bereich, in dem der jeweilige")
    print("     Button/Dialog immer erscheint.")
    print("  4. Bestätige die Vorschau mit 'Übernehmen'.")
    print("  5. ESC = Schritt überspringen (bestehender Wert bleibt erhalten).")
    print()
    input("  Enter drücken um zu starten …")
    print()

    # Bestehende Datei laden, damit übersprungene Schritte ihren alten Wert behalten
    try:
        with open(STEP_REGIONS_FILE, "r", encoding="utf-8") as f:
            regions = json.load(f)
    except Exception:
        regions = {}

    results = []
    for key, label in STEPS:
        print(f"\n► Nächster Suchbereich: {label}")
        try:
            outcome = capture_step_region(label)
        except Exception as exc:
            print(f"  FEHLER: {exc}")
            outcome = None

        if isinstance(outcome, tuple):
            x, y, w, h = outcome
            regions[key] = {"x": x, "y": y, "w": w, "h": h}
            print(f"  ✓  Bereich übernommen: {regions[key]}")
            results.append((key, label, True))
        else:
            print("  ÜBERSPRUNGEN – bestehender Wert (falls vorhanden) bleibt erhalten.")
            results.append((key, label, False))

    with open(STEP_REGIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(regions, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 55)
    print("  Ergebnis:")
    print("=" * 55)
    for key, label, ok in results:
        status = "OK        " if ok else "ÜBERSPRUNGEN"
        print(f"  [{status}]  {key:10s}  {label}")
    print(f"\n  Gespeichert in: {STEP_REGIONS_FILE}")
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
