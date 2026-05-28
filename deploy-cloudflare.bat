@echo off
title SANGAT Tools — Cloudflare Live Deploy
color 0A
cls

echo ============================================================
echo   SANGAT Tools — Cloudflare Tunnel Live Deploy
echo ============================================================
echo.

:: ── Step 1: Check Python ────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11 from python.org
    pause & exit /b 1
)
echo [OK] Python found

:: ── Step 2: Install Python dependencies if needed ───────────────
echo [..] Checking Python packages...
pip install -r requirements.txt -q --disable-pip-version-check
echo [OK] Python packages ready

:: ── Step 3: Download cloudflared if not installed ───────────────
where cloudflared >nul 2>&1
if errorlevel 1 (
    echo [..] cloudflared not found — downloading...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'"
    if errorlevel 1 (
        echo [ERROR] Download failed. Check your internet connection.
        pause & exit /b 1
    )
    echo [OK] cloudflared downloaded
    set CF=cloudflared.exe
) else (
    set CF=cloudflared
    echo [OK] cloudflared already installed
)

:: ── Step 4: Create required folders ─────────────────────────────
if not exist "static\uploads" mkdir "static\uploads"
if not exist "outputs" mkdir "outputs"

:: ── Step 5: Start Flask app in background ────────────────────────
echo.
echo [..] Starting Flask app on port 8080...
start "SANGAT Flask App" /min cmd /c "set PORT=8080 && set FLASK_ENV=production && set SECRET_KEY=cloudflare-tunnel-dev-key-change-me && gunicorn --config gunicorn.conf.py app:app"

:: Wait for Flask to start
timeout /t 4 /nobreak >nul
echo [OK] Flask app started on http://localhost:8080

:: ── Step 6: Start Cloudflare Tunnel ─────────────────────────────
echo.
echo ============================================================
echo   Starting Cloudflare Tunnel...
echo   Your LIVE URL will appear below in a few seconds.
echo   Share it with anyone — it works worldwide!
echo ============================================================
echo.

%CF% tunnel --url http://localhost:8080

:: If tunnel exits
echo.
echo [!] Tunnel stopped.
pause
