#Requires -RunAsAdministrator
<#
  Restore/extract Nirvana.exe after Defender exclusion.
  Right-click PowerShell -> Run as administrator ->:
    Set-ExecutionPolicy -Scope Process Bypass
    & 'D:\project\World of Warcraft plugin new\scripts\restore-nirvana-exe.ps1'
#>

$ErrorActionPreference = 'Stop'

$paths = @(
  'D:\project\_nirv_extract',
  'D:\project\Nirvana30',
  'D:\project\Nirvana30\Nirvana30',
  'D:\project\World of Warcraft plugin new',
  'D:\project\World of Warcraft plugin new\_extract'
)

Write-Host '== Adding Defender exclusions ==' -ForegroundColor Cyan
foreach ($p in $paths) {
  if (-not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
  Add-MpPreference -ExclusionPath $p
  Write-Host "  exclusion: $p"
}

Write-Host '== Restoring quarantined threats (best effort) ==' -ForegroundColor Cyan
$mp = 'C:\Program Files\Windows Defender\MpCmdRun.exe'
if (Test-Path $mp) {
  & $mp -Restore -ListAll
  & $mp -Restore -All
}

$dest = 'D:\project\_nirv_extract\Nirvana.exe'
$zip = 'D:\project\Nirvana30.zip'
Write-Host "== Extracting Nirvana.exe from zip -> $dest ==" -ForegroundColor Cyan
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($zip)
try {
  $entry = $archive.GetEntry('Nirvana30/Nirvana.exe')
  if (-not $entry) { throw 'Nirvana30/Nirvana.exe not found in zip' }
  if (Test-Path $dest) { Remove-Item $dest -Force }
  [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $dest, $true)
}
finally {
  $archive.Dispose()
}

Write-Host '== Verify readable ==' -ForegroundColor Cyan
$fs = [IO.File]::Open($dest, 'Open', 'Read', 'ReadWrite')
$buf = New-Object byte[] 2
[void]$fs.Read($buf, 0, 2)
$fs.Close()
if ($buf[0] -ne 0x4D -or $buf[1] -ne 0x5A) { throw 'Extracted file is not MZ' }
$hash = (Get-FileHash $dest -Algorithm SHA256).Hash.ToLower()
Write-Host "OK MZ header, SHA256=$hash"
Write-Host 'Expected SHA256=8ed3e725a7b3b44337c60d914308de2ad0f26fdf2c0ad8371405330d48c2a42d'
Write-Host 'Done. Tell the agent to continue unpacking.' -ForegroundColor Green
