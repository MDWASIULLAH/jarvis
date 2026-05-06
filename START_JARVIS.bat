@echo off
cd /d "%~dp0"
echo Starting Jarvis Local Core on http://127.0.0.1:8765 ...
start "Jarvis Local Core" cmd /k python main.py --bridge-only
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8765/index.html"
echo Jarvis opened from the Local Core URL. Keep the Jarvis Local Core window open.
