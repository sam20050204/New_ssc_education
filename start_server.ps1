# ========================================
# Network Server Launcher Script (PowerShell)
# Start Django Server for Network Access
# ========================================

Write-Host ""
Write-Host "============================================"
Write-Host " SSC Education - Network Server Launcher"
Write-Host "============================================"
Write-Host ""

# Change to the script directory so the launcher works from any cwd
Set-Location $PSScriptRoot

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env file from .env.example" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] Project directory: $(Get-Location)" -ForegroundColor Green
Write-Host "[OK] Configuration file (.env) found" -ForegroundColor Green
Write-Host ""

$lanIps = Get-CimInstance Win32_NetworkAdapterConfiguration |
    Where-Object { $_.IPEnabled -and $_.IPAddress } |
    ForEach-Object { $_.IPAddress } |
    Where-Object { $_ -match '^\d{1,3}(\.\d{1,3}){3}$' -and $_ -notlike '127.*' -and $_ -notlike '169.254.*' } |
    Select-Object -Unique

# Display server information
Write-Host "============================================"
Write-Host " SERVER INFORMATION"
Write-Host "============================================"
Write-Host "Server IP Address: 0.0.0.0 (all network interfaces)" -ForegroundColor Cyan
Write-Host "Server Port: 8000" -ForegroundColor Cyan
if ($lanIps) {
    Write-Host "LAN IP Address(es): $($lanIps -join ', ')" -ForegroundColor Cyan
    foreach ($ip in $lanIps) {
        Write-Host "Access from another computer: http://$ip`:8000" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARN] No LAN IPv4 address detected. Check the network connection." -ForegroundColor Yellow
}
Write-Host "Local access URL: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host ""
$firewallRule = netsh advfirewall firewall show rule name="SSC Education Django 8000" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Windows Firewall may still be blocking inbound traffic on port 8000." -ForegroundColor Yellow
    Write-Host '[WARN] Run this once in an Administrator terminal:' -ForegroundColor Yellow
    Write-Host '       netsh advfirewall firewall add rule name="SSC Education Django 8000" dir=in action=allow protocol=TCP localport=8000' -ForegroundColor Yellow
} else {
    Write-Host '[OK] Firewall rule "SSC Education Django 8000" already exists.' -ForegroundColor Green
}
Write-Host ""

# Prefer the project's virtual environment, then fall back to PATH
$pythonExe = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (Test-Path $pythonExe) {
    $pythonVersion = & $pythonExe --version 2>&1
    Write-Host "[OK] Python found in venv: $pythonVersion" -ForegroundColor Green
} else {
    try {
        $pythonVersion = python --version 2>&1
        $pythonExe = "python"
        Write-Host "[OK] Python found in PATH: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "Starting Django development server..." -ForegroundColor Green
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the Django development server
& $pythonExe manage.py runserver 0.0.0.0:8000

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to start server" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
