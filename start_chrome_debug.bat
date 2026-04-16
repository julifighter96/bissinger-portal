@echo off
REM Startet Chrome mit dem Portal – Browser bleibt dauerhaft offen
REM Kein Remote-Debugging notwendig, da der Bot rein auf Bildschirmebene arbeitet.

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
    --start-maximized ^
    "https://assistance.imhosting.de/elba_orders"

echo Chrome gestartet. Bitte einloggen, dann bot.py starten.
pause
