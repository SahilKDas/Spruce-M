param(
    [ValidateSet(0,1,2)][int]$Quality=0,
    [ValidateRange(20,600)][int]$Seconds=90
)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$godot=Join-Path $projectRoot '.tools/godot/Godot_v4.7-stable_win64_console.exe'
if (-not (Test-Path -LiteralPath $godot)) { throw 'Run Setup-HydroDrift.ps1 first.' }
& $godot --path (Join-Path $projectRoot 'game') -- "--benchmark=$Seconds" "--quality=$Quality"
if ($LASTEXITCODE -ne 0) { throw 'Benchmark failed; inspect the engine output.' }
$height=@(720,900,1080)[$Quality]
Get-Content -Raw -LiteralPath (Join-Path $projectRoot "benchmarks/performance_${height}p.json")
