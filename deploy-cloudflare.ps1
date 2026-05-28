# ============================================================
# SANGAT Tools — Cloudflare Tunnel Live Deploy (PowerShell)
# Run with:  .\deploy-cloudflare.ps1
# ============================================================

$Host.UI.RawUI.WindowTitle = "SANGAT Tools — Cloudflare Live"
Clear-Host

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SANGAT Tools — Cloudflare Tunnel Deploy" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$AppDir = $PSScriptRoot

# ── Step 1: Python check ────────────────────────────────────────
try { $pyver = python --version 2>&1; Write-Host "[OK] $pyver" -ForegroundColor Green }
catch { Write-Host "[ERROR] Python not found. Install from python.org" -ForegroundColor Red; pause; exit 1 }

# ── Step 2: Install dependencies ────────────────────────────────
Write-Host "[..] Checking Python packages..." -ForegroundColor Yellow
pip install -r "$AppDir\requirements.txt" -q --disable-pip-version-check
Write-Host "[OK] Python packages ready" -ForegroundColor Green

# ── Step 3: Get cloudflared ──────────────────────────────────────
$cfPath = "$AppDir\cloudflared.exe"
$cfCmd  = $null

if (Get-Command cloudflared -ErrorAction SilentlyContinue) {
    $cfCmd = "cloudflared"
    Write-Host "[OK] cloudflared already installed" -ForegroundColor Green
} elseif (Test-Path $cfPath) {
    $cfCmd = $cfPath
    Write-Host "[OK] cloudflared found locally" -ForegroundColor Green
} else {
    Write-Host "[..] Downloading cloudflared from Cloudflare..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest `
            -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" `
            -OutFile $cfPath `
            -UseBasicParsing
        $cfCmd = $cfPath
        Write-Host "[OK] cloudflared downloaded" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Could not download cloudflared. Check internet connection." -ForegroundColor Red
        pause; exit 1
    }
}

# ── Step 4: Create required directories ─────────────────────────
New-Item -ItemType Directory -Force -Path "$AppDir\static\uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "$AppDir\outputs"         | Out-Null

# ── Step 5: Start Flask app ──────────────────────────────────────
Write-Host ""
Write-Host "[..] Starting Flask app on port 8080..." -ForegroundColor Yellow

$env:PORT        = "8080"
$env:FLASK_ENV   = "production"
$env:SECRET_KEY  = "cf-tunnel-dev-key-change-in-production"

$flask = Start-Process -FilePath "gunicorn" `
    -ArgumentList "--config", "gunicorn.conf.py", "app:app" `
    -WorkingDirectory $AppDir `
    -PassThru -WindowStyle Minimized

Start-Sleep -Seconds 5

if ($flask.HasExited) {
    Write-Host "[WARN] gunicorn may not be in PATH — trying python app.py..." -ForegroundColor Yellow
    $flask = Start-Process -FilePath "python" `
        -ArgumentList "app.py" `
        -WorkingDirectory $AppDir `
        -PassThru -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

Write-Host "[OK] Flask app running (PID $($flask.Id))" -ForegroundColor Green

# ── Step 6: Launch Cloudflare Tunnel ────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Launching Cloudflare Tunnel..." -ForegroundColor Cyan
Write-Host "  Your LIVE URL will appear below (look for trycloudflare.com)" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

try {
    & $cfCmd tunnel --url http://localhost:8080
} finally {
    Write-Host ""
    Write-Host "[!] Tunnel stopped. Stopping Flask app..." -ForegroundColor Yellow
    if (-not $flask.HasExited) { Stop-Process -Id $flask.Id -Force -ErrorAction SilentlyContinue }
    Write-Host "[OK] All stopped." -ForegroundColor Green
}
