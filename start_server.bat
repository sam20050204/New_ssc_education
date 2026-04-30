@echo off
REM ========================================
REM Network Server Launcher Script
REM Start Django Server for Network Access
REM ========================================

echo.
echo ============================================
echo  SSC Education - Network Server Launcher
echo ============================================
echo.

REM Change to project directory
cd /d d:\Website\New_ssc_education

REM Check if project files exist
if not exist manage.py (
    echo.
    echo ERROR: manage.py not found!
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

echo ✓ Project directory: %CD%
echo ✓ Django project files found
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

REM Start the Django development server using full Python path
echo Starting Django development server...
echo Press CTRL+C to stop the server
echo.

C:/Users/Administrator/AppData/Local/Python/pythoncore-3.14-64/python.exe manage.py runserver 0.0.0.0:8000

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start server
    echo Make sure Python is installed and available in PATH
    pause
    exit /b 1
)

pause
