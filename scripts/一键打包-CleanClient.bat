@echo off
setlocal
cd /d "%~dp0.."
title CleanClient Packaging
echo ========================================
echo  CleanClient packaging starting...
echo  (Chinese details are in PowerShell log)
echo ========================================
echo.

where powershell >nul 2>nul
if errorlevel 1 (
  echo ERROR: powershell.exe not found in PATH.
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: python.exe not found in PATH.
  echo Install Python or open a terminal where "python" works.
  pause
  exit /b 1
)

powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_clean_client.ps1"
set ERR=%ERRORLEVEL%
echo.
if not "%ERR%"=="0" (
  echo PACKAGING FAILED. exit code=%ERR%
  pause
  exit /b %ERR%
)

echo PACKAGING DONE.
if exist "%cd%\release\CleanClient\CleanClient.exe" (
  echo EXE: %cd%\release\CleanClient\CleanClient.exe
  explorer "%cd%\release\CleanClient"
) else (
  echo WARNING: release\CleanClient\CleanClient.exe not found.
)
echo.
pause
endlocal
