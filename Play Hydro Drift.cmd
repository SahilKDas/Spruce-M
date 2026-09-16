@echo off
cd /d "%~dp0"
if not exist ".tools\godot\Godot_v4.7-stable_win64.exe" (
  echo Godot is missing. Run tools\Setup-HydroDrift.ps1 first.
  pause
  exit /b 1
)
start "Hydro Drift" ".tools\godot\Godot_v4.7-stable_win64.exe" --path "%~dp0game" --rendering-method mobile
