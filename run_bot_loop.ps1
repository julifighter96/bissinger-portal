# ---------------------------------------------------------------------------
# Startet ElbaBot.exe in einer Endlosschleife und startet ihn automatisch neu,
# sobald der Prozess beendet wird - egal ob durch Absturz, durch den internen
# Hang-Watchdog oder durch einen per ntfy.sh gesendeten "restart"-Befehl.
#
# Einrichtung: Diese Datei (statt einer direkten Verknuepfung zu ElbaBot.exe)
# in den Autostart-Ordner legen, z.B. als Verknuepfung mit folgendem Ziel:
#   powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "E:\bissinger-portal\run_bot_loop.ps1"
# ---------------------------------------------------------------------------

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$exePath = Join-Path $scriptDir "dist\ElbaBot.exe"
$logPath = Join-Path $scriptDir "run_bot_loop.log"

function Write-Log($message) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $message"
    Write-Host $line
    Add-Content -Path $logPath -Value $line
}

Write-Log "Supervisor gestartet. Ueberwache: $exePath"

while ($true) {
    if (-not (Test-Path $exePath)) {
        Write-Log "FEHLER: $exePath nicht gefunden. Warte 30s und pruefe erneut."
        Start-Sleep -Seconds 30
        continue
    }

    Write-Log "Starte ElbaBot.exe ..."
    $proc = Start-Process -FilePath $exePath -PassThru -WindowStyle Normal
    $proc.WaitForExit()
    Write-Log "ElbaBot.exe beendet (Exit-Code $($proc.ExitCode)). Neustart in 5s ..."
    Start-Sleep -Seconds 5
}
