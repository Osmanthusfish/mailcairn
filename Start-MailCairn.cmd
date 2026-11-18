@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 app.py --open-existing %*
) else (
  python app.py --open-existing %*
)
if errorlevel 1 (
  echo.
  echo MailCairn could not start. The error above explains why.
  echo If the archive is already open, close its older MailCairn window first.
  pause
  exit /b 1
)
