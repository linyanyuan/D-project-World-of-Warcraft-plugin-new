@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo [CleanClient] 精简打包中（已排除 torch / WebEngine 等，通常几分钟）...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_clean_client.ps1"
if errorlevel 1 (
  echo.
  echo 打包失败
  pause
  exit /b 1
)
echo.
echo 完成。请运行: release\CleanClient\CleanClient.exe
explorer "%cd%\release\CleanClient"
pause
