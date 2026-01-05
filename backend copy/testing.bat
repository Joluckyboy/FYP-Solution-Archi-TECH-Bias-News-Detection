@echo off
setlocal enabledelayedexpansion

rem Function to kill process using a specific port
call :kill_port 8011
call :kill_port 8012
call :kill_port 8013
call :kill_port 8014
call :kill_port 8015
call :kill_port 8016

rem Start database app
cd database
start /B uvicorn db_app:app --reload --port 8011
set DB_PID=%ERRORLEVEL%

rem Start sentiment app
cd ..\sentiment
start /B uvicorn app:app --reload --port 8012
set SENTIMENT_PID=%ERRORLEVEL%

rem Start emotion app
cd ..\emotion
start /B uvicorn app:app --reload --port 8013
set EMOTION_PID=%ERRORLEVEL%

rem Start propaganda app
cd ..\propaganda
start /B uvicorn app:app --reload --port 8014
set PROPAGANDA_PID=%ERRORLEVEL%

rem Start scraper app
cd ..\scraper
start /B gunicorn -w 4 -b 0.0.0.0:8015 app:app
set SCRAPER_PID=%ERRORLEVEL%

rem Start factcheck app
cd ..\fact-check
start /B uvicorn app.main:app --reload --port 8016
set FACTCHECK_PID=%ERRORLEVEL%

exit /b

:kill_port
set PORT=%1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT%') do (
    rem Kill the process with the given port
    taskkill /F /PID %%a
)
exit /b
