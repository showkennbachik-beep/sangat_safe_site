# ============================================================
# SANGAT Tools — Go Live with Permanent Cloudflare Tunnel
# Run this every time you want to go online.
# Requires: cloudflare-setup.ps1 to have been run once.
# ============================================================

$Host.UI.RawUI.WindowTitle = "SANGAT Tools — LIVE on Cloudflare"
Clear-Host

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SANGAT Tools — Starting Permanent Cloudflare Tunnel" -ForegroundColor Cyan
Write-Host "  URL: https://sangat-tools.is-a.dev" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$AppDir = $PSScriptRoot
$CfExe  = "$AppDir\cloudflared.exe"
$CfCmd  = if (Get-Command cloudflared -ErrorAction SilentlyContinue) { "cloudflared" } elseif (Test-Path $CfExe) { $CfExe } else { $null }

if (-not $CfCmd) {
    Write-Host "[ERROR] cloudflared not found. Run cloudflare-setup.ps1 first." -ForegroundColor Red
    pause; exit 1
}

# ── Start Flask app ──────────────────────────────────────────────
Write-Host "[..] Starting Flask app on port 8080..." -ForegroundColor Yellow

$env:PORT       = "8080"
$env:FLASK_ENV  = "production"
$env:SECRET_KEY = if ($env:SECRET_KEY) { $env:SECRET_KEY } else { "cf-change-this-in-production" }

New-Item -ItemType Directory -Force -Path "$AppDir\static\uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "$AppDir\outputs"         | Out-Null

# Try gunicorn first, fall back to python app.py
$flask = $null
try {
    $flask = Start-Process -FilePath "gunicorn" `
        -ArgumentList "--config", "gunicorn.conf.py", "app:app" `
        -WorkingDirectory $AppDir -PassThru -WindowStyle Minimized
} catch {
    $flask = Start-Process -FilePath "python" `
        -ArgumentList "app.py" `
        -WorkingDirectory $AppDir -PassThru -WindowStyle Minimized
}

Start-Sleep -Seconds 5
Write-Host "[OK] Flask app running (PID: $($flask.Id))" -ForegroundColor Green

# ── Start named tunnel ───────────────────────────────────────────
Write-Host ""
Write-Host "[..] Connecting Cloudflare Tunnel..." -ForegroundColor Yellow
Write-Host "     Your site will be live at:" -ForegroundColor White
Write-Host "     https://sangat-tools.is-a.dev" -ForegroundColor Green
Write-Host ""
Write-Host "     Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

try {
    & $CfCmd tunnel run sangat-tools
} finally {
    Write-Host ""
    Write-Host "[!] Stopping..." -ForegroundColor Yellow
    if ($flask -and -not $flask.HasExited) {
        Stop-Process -Id $flask.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] All services stopped." -ForegroundColor Green
    pause
}
