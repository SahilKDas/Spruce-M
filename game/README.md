# Hydro Drift — first playable prototype

From the repository root, double-click **Play Hydro Drift.cmd**.

The game launches fullscreen in 16:9, capped at 60 FPS. The default Native preset renders the 3D scene at 1920 × 1080 with 2× MSAA edge smoothing. The interface is rasterized at display resolution with grayscale font antialiasing and quarter-pixel positioning. Performance (720p with FXAA) and Balanced (900p with 2× MSAA) remain available. This display update selects Native once; later graphics selections are saved. F11 switches fullscreen/windowed. Other aspect ratios use letterboxing.

## Play

Choose one of eight armored knights and three watercraft, then start an eight-racer race or a solo time trial. Follow the buoy course around Sunbeam Lagoon. Complete all 20 checkpoints in order for each of three laps. The minimap shows your heading, opponents, and the next checkpoint.

| Action | Keyboard | Controller |
| --- | --- | --- |
| Throttle / brake / reverse | W / S or up / down | Right / left trigger |
| Steer | A / D or left / right | Left stick |
| Drift; release to earn boost | Shift | Right bumper |
| Spend boost | Ctrl or E | X |
| Hop | Space | A |
| Recover at last checkpoint | R | Y |
| Pause | Escape | Start |
| Mute | M | Pause menu |
| Performance overlay | F3 | — |
| Fullscreen | F11 | — |

Collect turquoise batteries to refill boost. Orange ramps offer a jump route. Rider fingers are fixed to the hands; body rigs retain bendable elbows and knees. The prototype uses a baked riding pose and whole-rider lean; a full animation set is still to come.

## Current scope

This is the handling and race-loop prototype: one short course, four-point buoyancy, drift/boost/hop, seven AI opponents, three craft handling profiles, checkpoints/laps, recovery, chase camera, wakes, pickups, minimap, pause/restart/results, and saved selections and time-trial records.

Scenery, water, synthetic engine audio, AI tactics, and riding animation are preliminary. The six production courses, cups, other items, cosmetics, rebinding, vibration, accessibility options, and final sound/animation passes remain planned. A higher graphics preset is an option, not a promise of 60 FPS.

## Rebuild runtime art

The current editable Blender sources are `assets/source/Hydro_Drift_Knights.blend`, `Hydro_Drift_Watercraft_v3.blend`, and `Hydro_Drift_Environment_v3.blend`. Runtime meshes are generated into ignored `game/art`: approximately 160,000 triangles for the local knight, 22,000 per opponent, and 120,000/40,000 for local/opponent craft before Godot mesh LODs. All knights use 20-bone body rigs and static modeled fingers. The anatomical mesh is from Blender's CC0 human base-mesh bundle; armor, rigs, watercraft, and scenery are custom Blender work. See `assets/vendor/README.md` for attribution.

```powershell
./tools/Setup-HydroDrift.ps1
```

Setup uses the locally downloaded Godot 4.7 Windows ZIP and installed Blender 5.1. It exports the committed source art, then imports the Godot project. The portable engine lives in ignored `.tools/godot`; asset caches live in ignored `game/.godot`. No installer or export templates are needed to play through the launcher.

## Validation

Run from the repository root:

```powershell
$godot = './.tools/godot/Godot_v4.7-stable_win64_console.exe'
& $godot --headless --path game --script res://tests/rules_test.gd
& $godot --headless --path game --script res://tests/controls_test.gd
& $godot --headless --path game --script res://tests/three_lap_test.gd
& $godot --headless --path game --script res://tests/integration_test.gd
& $godot --path game -- --benchmark=90 --quality=0
```

Rendered benchmarks retain the 60 FPS cap and skip a 10-second warm-up. Presets are `0` (720p), `1` (900p), and `2` (1080p). Results go to `benchmarks/performance_720p.json` and corresponding resolution files. Renderer allocation counters exclude driver and desktop GPU allocations. Headless tests accelerate simulation while preserving the gameplay physics step; their FPS does not measure GPU performance.

See `../benchmarks/README.md` for measurements and remaining acceptance criteria.

## Handling update — September 18

Driving uses the available MIT-licensed mk7re velocity update, with Hydro Drift tuning for watercraft acceleration, lateral grip, locked drift direction, and two timed mini-turbo levels. This is a partial adaptation, not exact Mario Kart 7 physics; see [source and license](third_party/mk7re/README.md).

Physics interpolation, an interpolated chase camera, and a continuously updated wake head smooth movement between simulation ticks. Recovery resets interpolation. Esc opens the pause menu; Exit Game requires confirmation, and Back returns to the paused game.

Additional checks: `handling_test.gd`, `motion_test.gd`, and `exit_test.gd` in `game/tests`.
