@echo off
setlocal
cd /d "%~dp0"
rem Use a console interpreter for source fallback so startup errors stay visible.
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 "%~dp0desktop.py" %*
) else (
  python "%~dp0desktop.py" %*
)
if errorlevel 1 (
  echo.
  echo MailCairn could not start. The error above explains why.
  echo Python 3.11 or newer with Tkinter is required for the source version.
  echo You can also use the packaged MailCairn.exe without installing Python.
  pause
  exit /b 1
)
