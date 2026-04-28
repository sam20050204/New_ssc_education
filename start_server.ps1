# ========================================
# Network Server Launcher Script (PowerShell)
# Start Django Server for Network Access
# ========================================

Write-Host ""
Write-Host "============================================"
Write-Host " SSC Education - Network Server Launcher"
Write-Host "============================================"
Write-Host ""

# Change to project directory
Set-Location "e:\Projects\New_ssc_education"

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env file from .env.example" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Project directory: $(Get-Location)" -ForegroundColor Green
Write-Host "✓ Configuration file (.env) found" -ForegroundColor Green
Write-Host ""

# Display server information
Write-Host "============================================"
Write-Host " SERVER INFORMATION"
Write-Host "============================================"
Write-Host "Server IP Address: 192.168.29.47" -ForegroundColor Cyan
Write-Host "Server Port: 8000" -ForegroundColor Cyan
Write-Host "Access URL: http://192.168.29.47:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "⚠️  Make sure firewall allows port 8000!" -ForegroundColor Yellow
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Starting Django development server..." -ForegroundColor Green
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the Django development server
python manage.py runserver 0.0.0.0:8000

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to start server" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
