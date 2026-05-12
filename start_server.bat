@echo off
setlocal
REM ========================================
REM SSC Education ERP Launcher Script
REM Starts Django with local development settings
REM ========================================

echo.
echo ============================================
echo  SSC Education ERP - Server Launcher
echo ============================================
echo.

REM Change to this script's directory so the launcher works from any cwd
cd /d "%~dp0"

REM Check if project files exist
if not exist manage.py (
    echo.
    echo ERROR: manage.py not found!
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

echo [OK] Project directory: %CD%
echo [OK] Django project files found
echo.

REM Warn if .env is missing. Development can still boot from defaults,
REM but local overrides like ADMIN_URL or security toggles will be absent.
if exist .env (
    echo [OK] Configuration file .env found
) else (
    echo [WARN] .env not found. Using settings defaults and any persisted local secret key.
)
echo.

REM Prefer the project's virtual environment, then fall back to PATH
set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
    echo [OK] Using virtual environment Python
) else (
    set "PYTHON_EXE=python"
    echo [WARN] venv\Scripts\python.exe not found, using Python from PATH
)

REM Use development settings by default
set "DJANGO_SETTINGS_MODULE=Project.settings.dev"

REM Ensure runtime directories exist for logging and uploaded files
if not exist logs (
    mkdir logs
    echo [OK] Created logs directory
)
if not exist media (
    mkdir media
    echo [OK] Created media directory
)

REM Run checks before startup
echo Running Django system checks...
"%PYTHON_EXE%" manage.py check
if errorlevel 1 (
    echo.
    echo ERROR: Django system checks failed
    pause
    exit /b 1
)

REM Apply migrations so the new ERP foundation models are available
echo Running database migrations...
"%PYTHON_EXE%" manage.py migrate
if errorlevel 1 (
    echo.
    echo ERROR: Database migration failed
    pause
    exit /b 1
)

REM Display server information
echo ============================================
echo  SERVER INFORMATION
echo ============================================
echo Server IP Address: 0.0.0.0 (accessible on all network interfaces)
echo Server Port: 8000
echo Local access URL: http://127.0.0.1:8000 or http://localhost:8000
echo Health URL: http://127.0.0.1:8000/health/
echo.
echo To open this website from another computer, find this PC's LAN IP with:
echo        ipconfig
echo Then open: http://YOUR_LAN_IP:8000
echo.
netsh advfirewall firewall show rule name="SSC Education Django 8000" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Windows Firewall may still be blocking inbound traffic on port 8000.
    echo [WARN] Run this command in an Administrator terminal once:
    echo        netsh advfirewall firewall add rule name^="SSC Education Django 8000" dir^=in action^=allow protocol^=TCP localport^=8000
) else (
    echo [OK] Firewall rule "SSC Education Django 8000" already exists.
)
echo.

echo Starting Django development server...
echo Press CTRL+C to stop the server
echo.

"%PYTHON_EXE%" manage.py runserver 0.0.0.0:8000

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start server
    echo Make sure Python is installed and dependencies are available
    pause
    exit /b 1
)

pause
