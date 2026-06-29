@echo off
title Canon Bot
cd /d "%~dp0"

:loop
echo [%date% %time%] Starting bot... >> bot_run.log
".venv\Scripts\python.exe" run_agent_telegram.py >> bot_run.log 2>&1
echo [%date% %time%] Bot exited (code %errorlevel%). Restarting in 5s... >> bot_run.log
timeout /t 5 /nobreak >nul
goto loop
