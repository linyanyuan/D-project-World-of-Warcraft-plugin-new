#Requires -Version 5.1
<#
  One-click lean package for clean_client -> dist/CleanClient/CleanClient.exe

  Usage:
    powershell -ExecutionPolicy Bypass -File "...\scripts\build_clean_client.ps1"

  Or double-click: scripts\yi-jian-packaging bat (Chinese filename OK)
#>
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root 'clean_client\app.py'))) {
  $Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}
Set-Location $Root
Write-Host "Project root: $Root" -ForegroundColor Cyan

$Python = (Get-Command python -ErrorAction Stop).Source
Write-Host "Python: $Python"

# Ensure bundler
python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing pyinstaller..." -ForegroundColor Yellow
  python -m pip install -U 'pyinstaller>=6.0'
}

Write-Host "Checking runtime deps..." -ForegroundColor Cyan
python -m pip install -r (Join-Path $Root 'clean_client\requirements.txt') | Out-Null

$Dist = Join-Path $Root 'dist'
$Work = Join-Path $Root 'build\pyinstaller'
$Name = 'CleanClient'
$Spec = Join-Path $PSScriptRoot 'CleanClient.spec'
$ConfigJson = Join-Path $Root 'clean_client\config\default.json'
$ProfileJson = Join-Path $Root 'clean_client\profiles\unholy_default.json'

if (-not (Test-Path $Spec)) { throw "Missing spec: $Spec" }
if (-not (Test-Path $ConfigJson)) { throw "Missing config: $ConfigJson" }
if (-not (Test-Path $ProfileJson)) { throw "Missing profile: $ProfileJson" }

$OutApp = Join-Path $Dist $Name
if (Test-Path $OutApp) {
  Write-Host "Cleaning old dist\$Name ..." -ForegroundColor Yellow
  Remove-Item -Recurse -Force $OutApp
}
if (Test-Path $Work) {
  Write-Host "Cleaning old build\pyinstaller ..." -ForegroundColor Yellow
  Remove-Item -Recurse -Force $Work
}
New-Item -ItemType Directory -Force -Path $Work | Out-Null

Write-Host ""
Write-Host "Running lean PyInstaller (torch/WebEngine excluded)..." -ForegroundColor Cyan
Write-Host "Spec: $Spec"
$sw = [System.Diagnostics.Stopwatch]::StartNew()

& python -m PyInstaller --noconfirm --clean --distpath $Dist --workpath $Work $Spec

if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$sw.Stop()
Write-Host ("PyInstaller finished in {0:n1} seconds" -f $sw.Elapsed.TotalSeconds) -ForegroundColor Green

$ExeName = $Name + '.exe'
$Exe = Join-Path $OutApp $ExeName
if (-not (Test-Path $Exe)) {
  throw "Expected exe not found: $Exe"
}

$ShortcutDir = Join-Path $Root 'release'
New-Item -ItemType Directory -Force -Path $ShortcutDir | Out-Null
$ReleaseApp = Join-Path $ShortcutDir $Name
Get-Process -Name $Name -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500
if (Test-Path $ReleaseApp) {
  Write-Host "Cleaning old release\$Name ..." -ForegroundColor Yellow
  Remove-Item -Recurse -Force $ReleaseApp
}
Copy-Item -Recurse -Force $OutApp $ReleaseApp

# Ship WoW addon + docs with the release folder (for GitHub Releases / friends)
$AddonSrc = Join-Path $Root 'addon\AutoPlayer'
$AddonDst = Join-Path $ReleaseApp 'addon\AutoPlayer'
if (-not (Test-Path $AddonSrc)) {
  throw "Missing WoW addon folder: $AddonSrc"
}
if (Test-Path $AddonDst) {
  Remove-Item -Recurse -Force $AddonDst
}
New-Item -ItemType Directory -Force -Path (Join-Path $ReleaseApp 'addon') | Out-Null
Copy-Item -Recurse -Force $AddonSrc $AddonDst
Write-Host "Bundled addon: $AddonDst" -ForegroundColor Cyan

$DocsDir = Join-Path $ReleaseApp 'docs'
New-Item -ItemType Directory -Force -Path $DocsDir | Out-Null
$ManualSrc = Join-Path $Root 'docs\使用手册-clean_client.md'
if (Test-Path $ManualSrc) {
  Copy-Item -Force $ManualSrc (Join-Path $DocsDir '使用手册-clean_client.md')
}
$DocxManual = Join-Path $Root 'docs\CleanClient-小白完整使用手册.docx'
if (Test-Path $DocxManual) {
  Copy-Item -Force $DocxManual (Join-Path $DocsDir 'CleanClient-小白完整使用手册.docx')
}
$GuideSrc = Join-Path $PSScriptRoot 'release_install_guide.txt'
if (Test-Path $GuideSrc) {
  Copy-Item -Force $GuideSrc (Join-Path $ReleaseApp '请先读-安装说明.txt')
}

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
Write-Host "PACKAGING OK" -ForegroundColor Green
Write-Host ("Full bundle: {0}  ({1} MB)" -f $OutApp, $distMB)
Write-Host ("Double-click: {0}\CleanClient.exe  ({1} MB)" -f $ReleaseApp, $relMB)
Write-Host "Keep the whole CleanClient folder together (do not copy only the .exe)."
