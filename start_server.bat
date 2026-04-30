@echo off
setlocal
REM ========================================
REM Network Server Launcher Script
REM Start Django Server for Network Access
REM ========================================

echo.
echo ============================================
echo  SSC Education - Network Server Launcher
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

REM Display server information
echo ============================================
echo  SERVER INFORMATION
echo ============================================
echo Server IP Address: 0.0.0.0 (accessible on all network interfaces)
echo Server Port: 8000
echo Access URL: http://127.0.0.1:8000 or http://localhost:8000
echo.
echo Make sure firewall allows port 8000 for network access!
echo.

REM Prefer the project's virtual environment, then fall back to PATH
echo Starting Django development server...
echo Press CTRL+C to stop the server
echo.

set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" manage.py runserver 0.0.0.0:8000
) else (
    python manage.py runserver 0.0.0.0:8000
)

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start server
    echo Make sure Python is installed or that venv\Scripts\python.exe exists
    pause
    exit /b 1
)

pause
