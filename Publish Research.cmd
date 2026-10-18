@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto python
py -3 publisher.py
goto done
:python
python publisher.py
:done
echo.
pause
