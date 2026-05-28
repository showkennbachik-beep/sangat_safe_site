# ============================================================
# SANGAT Tools — Cloudflare Permanent Tunnel Setup
# Run this ONCE to create your permanent tunnel.
# After this, use: .\cloudflare-start.ps1   (to go live)
# ============================================================

$Host.UI.RawUI.WindowTitle = "SANGAT — Cloudflare Setup"
Clear-Host

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SANGAT Tools — Cloudflare Permanent Tunnel Setup" -ForegroundColor Cyan
Write-Host "  This runs ONCE. After this just use cloudflare-start.ps1" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$AppDir  = $PSScriptRoot
$CfDir   = "$env:USERPROFILE\.cloudflared"
$CfExe   = "$AppDir\cloudflared.exe"

# ── Step 1: Download cloudflared ─────────────────────────────────
if (Get-Command cloudflared -ErrorAction SilentlyContinue) {
    $CfCmd = "cloudflared"
    Write-Host "[OK] cloudflared already installed system-wide" -ForegroundColor Green
} elseif (Test-Path $CfExe) {
    $CfCmd = $CfExe
    Write-Host "[OK] cloudflared found in project folder" -ForegroundColor Green
} else {
    Write-Host "[..] Downloading cloudflared from Cloudflare..." -ForegroundColor Yellow
    Invoke-WebRequest `
        -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" `
        -OutFile $CfExe -UseBasicParsing
    $CfCmd = $CfExe
    Write-Host "[OK] cloudflared downloaded" -ForegroundColor Green
}

# ── Step 2: Login to Cloudflare ──────────────────────────────────
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host " STEP 1/3 — Login to your Cloudflare account" -ForegroundColor Yellow
Write-Host " Your browser will open. Click the domain you want to use." -ForegroundColor Yellow
Write-Host " (If you have NO domain yet, press Ctrl+C and read the note)" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press ENTER to open Cloudflare login in your browser..."
Read-Host

& $CfCmd tunnel login

if (-not (Test-Path "$CfDir\cert.pem")) {
    Write-Host ""
    Write-Host "[!] Login may not have completed. Check your browser." -ForegroundColor Red
    Write-Host "    If you have no domain in Cloudflare yet, see the NOTE at the bottom." -ForegroundColor Red
    Write-Host ""
}

# ── Step 3: Create the named tunnel ──────────────────────────────
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host " STEP 2/3 — Creating permanent tunnel named 'sangat-tools'" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host ""

$tunnelOutput = & $CfCmd tunnel create sangat-tools 2>&1
Write-Host $tunnelOutput

# Extract UUID from output  (line like: "Created tunnel sangat-tools with id a1b2c3...")
$uuid = ($tunnelOutput | Select-String -Pattern '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}').Matches.Value | Select-Object -First 1

if (-not $uuid) {
    # Try to list tunnels and grab UUID
    $listOut = & $CfCmd tunnel list 2>&1
    $uuid = ($listOut | Select-String -Pattern 'sangat-tools\s+([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})').Matches.Groups[1].Value
}

if ($uuid) {
    Write-Host ""
    Write-Host "[OK] Tunnel UUID: $uuid" -ForegroundColor Green
} else {
    Write-Host "[WARN] Could not auto-detect UUID. Run: cloudflared tunnel list" -ForegroundColor Yellow
    $uuid = Read-Host "  Enter your tunnel UUID manually"
}

# ── Step 4: Write cloudflared config ─────────────────────────────
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host " STEP 3/3 — Writing tunnel config files" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow

$credFile = "$CfDir\$uuid.json"
$configContent = @"
tunnel: $uuid
credentials-file: $credFile

ingress:
  - hostname: sangat-tools.is-a.dev
    service: http://localhost:8080
  - service: http_status:404
"@

$configPath = "$CfDir\config.yml"
$configContent | Out-File -FilePath $configPath -Encoding utf8
Write-Host "[OK] Config written to: $configPath" -ForegroundColor Green

# Also write a local copy
$configContent | Out-File -FilePath "$AppDir\cloudflare-config.yml" -Encoding utf8
Write-Host "[OK] Local copy: $AppDir\cloudflare-config.yml" -ForegroundColor Green

# ── Step 5: Generate is-a.dev registration file ──────────────────
$isADevJson = @"
{
  "description": "SANGAT Tools — Free PDF and Image toolkit",
  "repo": "https://github.com/showkennbachik-beep/sangat_safe_site",
  "owner": {
    "username": "showkennbachik-beep",
    "email": "duroog3@gmail.com"
  },
  "record": {
    "CNAME": "$uuid.cfargotunnel.com"
  }
}
"@

$isADevPath = "$AppDir\is-a-dev-sangat-tools.json"
$isADevJson | Out-File -FilePath $isADevPath -Encoding utf8

Write-Host "[OK] is-a.dev registration file: $isADevPath" -ForegroundColor Green

# ── Done ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Tunnel UUID : $uuid" -ForegroundColor Cyan
Write-Host "  Config file : $configPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "  NEXT STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Get your FREE domain (sangat-tools.is-a.dev):" -ForegroundColor White
Write-Host "     a. Go to: https://github.com/is-a-dev/register" -ForegroundColor Gray
Write-Host "     b. Fork the repo" -ForegroundColor Gray
Write-Host "     c. Create file: domains/sangat-tools.json" -ForegroundColor Gray
Write-Host "     d. Paste the contents of: is-a-dev-sangat-tools.json" -ForegroundColor Gray
Write-Host "     e. Submit a Pull Request — approved in 1-2 days" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. While waiting, go live NOW with a temporary URL:" -ForegroundColor White
Write-Host "     Run: .\deploy-cloudflare.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. After is-a.dev PR is approved, go live permanently:" -ForegroundColor White
Write-Host "     Run: .\cloudflare-start.ps1" -ForegroundColor Gray
Write-Host ""

Write-Host "NOTE: If you have NO domain in Cloudflare yet," -ForegroundColor DarkYellow
Write-Host "      the login step still works — cloudflared uses" -ForegroundColor DarkYellow
Write-Host "      your account to manage the tunnel certificate." -ForegroundColor DarkYellow
Write-Host "      You do NOT need a domain added to Cloudflare." -ForegroundColor DarkYellow
Write-Host ""
pause
