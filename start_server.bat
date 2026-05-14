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

REM Attempt to locate a Python executable in common virtualenvs or PATH
echo Starting Django development server...
echo Press CTRL+C to stop the server
echo.

setlocal enabledelayedexpansion

set "PY_CAND="
if exist "%~dp0.venv\Scripts\python.exe" set "PY_CAND=%~dp0.venv\Scripts\python.exe"
if not defined PY_CAND if exist "%~dp0venv\Scripts\python.exe" set "PY_CAND=%~dp0venv\Scripts\python.exe"
if not defined PY_CAND if exist "%~dp0env\Scripts\python.exe" set "PY_CAND=%~dp0env\Scripts\python.exe"

if not defined PY_CAND (
    for /f "delims=" %%P in ('where python 2^>nul') do (
        if not defined PY_CAND set "PY_CAND=%%P"
    )
)

if not defined PY_CAND (
    for /f "delims=" %%Q in ('where py 2^>nul') do (
        if not defined PY_CAND set "PY_CAND=py"
    )
)

if defined PY_CAND (
    echo Using Python: %PY_CAND%
    echo.
    
    REM Check if virtual environment is active, if not try to activate it
    if exist "%~dp0.venv\Scripts\activate.bat" (
        echo Activating virtual environment from .venv...
        call "%~dp0.venv\Scripts\activate.bat"
    ) else if exist "%~dp0venv\Scripts\activate.bat" (
        echo Activating virtual environment from venv...
        call "%~dp0venv\Scripts\activate.bat"
    ) else if exist "%~dp0env\Scripts\activate.bat" (
        echo Activating virtual environment from env...
        call "%~dp0env\Scripts\activate.bat"
    )
    
    echo.
    echo Checking dependencies...
    if "%PY_CAND%"=="py" (
        py -3 -m pip list >nul 2>&1 || (
            echo ERROR: pip not found. Virtual environment may not be properly set up.
            pause
            exit /b 1
        )
    ) else (
        "%PY_CAND%" -m pip list >nul 2>&1 || (
            echo ERROR: pip not found. Virtual environment may not be properly set up.
            pause
            exit /b 1
        )
    )
    
    echo [OK] Dependencies available
    echo.
    
    echo Running database migrations...
    if "%PY_CAND%"=="py" (
        py -3 manage.py migrate
    ) else (
        "%PY_CAND%" manage.py migrate
    )
    
    if errorlevel 1 (
        echo.
        echo ERROR: Database migration failed. See output above.
        pause
        exit /b 1
    )
    
    echo.
    echo ============================================
    echo  Starting Django Development Server
    echo ============================================
    echo.
    if "%PY_CAND%"=="py" (
        py -3 manage.py runserver 0.0.0.0:8000
    ) else (
        "%PY_CAND%" manage.py runserver 0.0.0.0:8000
    )
    if errorlevel 1 (
        echo.
        echo ERROR: Server exited with an error. See output above.
        pause
        exit /b 1
    )
    exit /b 0
)

echo.
echo ERROR: Could not find a Python executable.
echo Please install Python 3 and ensure one of the following is available:
echo  - A virtual environment at .venv\Scripts\python.exe or venv\Scripts\python.exe
echo  - The 'python' command on your PATH (run 'where python' to check)
echo  - The 'py' launcher (Windows Python launcher) which supports 'py -3'
echo.
pause
exit /b 1
