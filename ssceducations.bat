@echo off
cd /d E:\Projects\New_ssc_education

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting Django Server...
start cmd /k python manage.py runserver

timeout /t 3 >nul

echo Opening Browser...
start http://127.0.0.1:8000
