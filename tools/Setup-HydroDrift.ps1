param([string]$GodotZip = "$env:USERPROFILE\Downloads\Godot_v4.7-stable_win64.exe.zip")
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$godotDir = Join-Path $projectRoot '.tools\godot'
if (-not (Test-Path -LiteralPath $GodotZip)) { throw 'Pass -GodotZip with the path to the official Godot 4.7 Windows archive.' }
Expand-Archive -LiteralPath $GodotZip -DestinationPath $godotDir -Force
$blenderPath = 'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe'
if (-not (Test-Path -LiteralPath $blenderPath)) { throw 'Blender 5.1 is required to prepare runtime models.' }
& $blenderPath --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'prepare_runtime_assets.py')
if ($LASTEXITCODE -ne 0) { throw 'Runtime asset generation failed.' }
& (Join-Path $godotDir 'Godot_v4.7-stable_win64_console.exe') --headless --editor --path (Join-Path $projectRoot 'game') --import
if ($LASTEXITCODE -ne 0) { throw 'Godot import failed.' }
