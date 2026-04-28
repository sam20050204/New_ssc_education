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
cd /d e:\Projects\New_ssc_education

REM Check if .env file exists
if not exist .env (
    echo.
    echo ERROR: .env file not found!
    echo Please create .env file from .env.example
    pause
    exit /b 1
)

echo ✓ Project directory: %CD%
echo ✓ Configuration file (.env) found
echo.

REM Display server information
echo ============================================
echo  SERVER INFORMATION
echo ============================================
echo Server IP Address: 192.168.29.47
echo Server Port: 8000
echo Access URL: http://192.168.29.47:8000
echo.
echo Make sure firewall allows port 8000!
echo.

REM Start the Django development server
echo Starting Django development server...
echo Press CTRL+C to stop the server
echo.

python manage.py runserver 0.0.0.0:8000

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start server
    echo Make sure Python is installed and available in PATH
    pause
    exit /b 1
)

pause
