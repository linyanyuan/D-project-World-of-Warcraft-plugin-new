#Requires -Version 5.1
<#
  One-click lean package for clean_client → dist/CleanClient/CleanClient.exe

  Usage:
    powershell -ExecutionPolicy Bypass -File "D:\project\World of Warcraft plugin new\scripts\build_clean_client.ps1"

  Or double-click: scripts\一键打包-CleanClient.bat
#>
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root 'clean_client\app.py'))) {
  $Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}
Set-Location $Root
Write-Host "项目根目录: $Root" -ForegroundColor Cyan

$Python = (Get-Command python -ErrorAction Stop).Source
Write-Host "Python: $Python"

# Ensure bundler
python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "正在安装 pyinstaller..." -ForegroundColor Yellow
  python -m pip install -U 'pyinstaller>=6.0'
}

# Runtime deps only (do not install the whole host ML stack)
Write-Host "检查运行依赖..." -ForegroundColor Cyan
python -m pip install -r (Join-Path $Root 'clean_client\requirements.txt') | Out-Null

$Dist = Join-Path $Root 'dist'
$Work = Join-Path $Root 'build\pyinstaller'
$Name = 'CleanClient'
$Spec = Join-Path $PSScriptRoot 'CleanClient.spec'
$ConfigJson = Join-Path $Root 'clean_client\config\default.json'
$ProfileJson = Join-Path $Root 'clean_client\profiles\unholy_default.json'

if (-not (Test-Path $Spec)) { throw "缺少打包规格文件: $Spec" }
if (-not (Test-Path $ConfigJson)) { throw "缺少配置: $ConfigJson" }
if (-not (Test-Path $ProfileJson)) { throw "缺少循环配置: $ProfileJson" }

# Clean previous bundle of this app only
$OutApp = Join-Path $Dist $Name
if (Test-Path $OutApp) {
  Write-Host "清理旧的 dist\$Name ..." -ForegroundColor Yellow
  Remove-Item -Recurse -Force $OutApp
}
if (Test-Path $Work) {
  Write-Host "清理旧的 build\pyinstaller ..." -ForegroundColor Yellow
  Remove-Item -Recurse -Force $Work
}
New-Item -ItemType Directory -Force -Path $Work | Out-Null

Write-Host ""
Write-Host "开始 PyInstaller 精简打包（已排除 torch/scipy/WebEngine 等）..." -ForegroundColor Cyan
Write-Host "规格文件: $Spec"
$sw = [System.Diagnostics.Stopwatch]::StartNew()

& python -m PyInstaller `
  --noconfirm `
  --clean `
  --distpath $Dist `
  --workpath $Work `
  $Spec

if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller 失败，退出码 $LASTEXITCODE"
}

$sw.Stop()
Write-Host ("PyInstaller 耗时: {0:n1} 秒" -f $sw.Elapsed.TotalSeconds) -ForegroundColor Green

$Exe = Join-Path $OutApp "$Name.exe"
if (-not (Test-Path $Exe)) {
  throw "未找到输出: $Exe"
}

# Copy whole folder so dependencies stay next to exe
$ShortcutDir = Join-Path $Root 'release'
New-Item -ItemType Directory -Force -Path $ShortcutDir | Out-Null
$ReleaseApp = Join-Path $ShortcutDir $Name
Get-Process -Name $Name -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500
if (Test-Path $ReleaseApp) {
  Write-Host "清理旧的 release\$Name ..." -ForegroundColor Yellow
  Remove-Item -Recurse -Force $ReleaseApp
}
Copy-Item -Recurse -Force $OutApp $ReleaseApp

function Get-DirSizeMB([string]$Path) {
  if (-not (Test-Path $Path)) { return 0 }
  $bytes = (Get-ChildItem -LiteralPath $Path -Recurse -File -ErrorAction SilentlyContinue |
    Measure-Object -Property Length -Sum).Sum
  if ($null -eq $bytes) { return 0 }
  return [math]::Round($bytes / 1MB, 1)
}

$distMB = Get-DirSizeMB $OutApp
$relMB = Get-DirSizeMB $ReleaseApp

Write-Host ""
Write-Host "打包完成" -ForegroundColor Green
Write-Host "完整目录: $OutApp  ($distMB MB)"
Write-Host "可双击:   $ReleaseApp\CleanClient.exe  ($relMB MB)"
Write-Host "说明: 请保持整个 CleanClient 文件夹完整，不要只拷贝单个 exe。"
Write-Host "若仍偏大，多半是本机还装了无关包被误收集；本脚本已强制排除 torch 等大火腿。"
