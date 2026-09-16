# Hydro Drift prototype validation

Measured on September 15, 2026, using the installed **NVIDIA GeForce MX550**, Godot **4.7 stable**, Vulkan Mobile renderer, and eight simulated racers. Display output was **1920 × 1080 fullscreen**, 16:9, with **VSync and a 60 FPS cap**. The default remains Performance (720p internal).

## Final rendered runs

| Measurement | Performance | Balanced |
| --- | ---: | ---: |
| Internal 3D resolution | 1280 × 720 | 1600 × 900 |
| Run duration | 90 seconds | 90 seconds |
| Warm-up excluded | 10 seconds | 10 seconds |
| Average FPS | 60.00 | 60.00 |
| 1% low FPS | 55.80 | 55.60 |
| Peak draw calls | 728 | 867 |
| Peak rendered primitives | 160,657 | 175,867 |
| Peak renderer allocations | 122.7 MiB | 152.7 MiB |
| Automatic recoveries | 0 | 0 |

Raw results: [720p](performance_720p.json), [900p](performance_900p.json). Frame intervals use a wall clock. The 1% low is the inverse of the average duration of the slowest 1% of sampled frames. Tiny average values above 60 reflect timer/limiter variation around the cap.

Screenshot capture occurs during warm-up. An earlier version captured after warm-up and introduced a roughly 218 ms GPU readback stall into its own measurement; those preliminary low-percentile figures were invalid for normal play and are superseded by these runs. Normal gameplay does not capture screenshots.

Renderer allocations exclude driver, operating-system, desktop and other application allocations; they are not a measurement of total dedicated VRAM usage. A separate in-flight check observed approximately 589 MiB process working set and 602 MiB peak working set. The entire working folder, including Git, portable Godot, generated art and import caches, was approximately **0.401 GiB / 0.43 GB**, below the user's 10 GB allowance.

## Functional checks

- **20 automated one-lap, eight-racer races completed.** Accelerated headless simulation retained the same physics step as gameplay. Details: [integration.json](integration.json).
- All eight rider imports, race and time-trial entry, pause/resume, checkpoint-preserving recovery, results and return to selection passed.
- All 20 gates accepted forward crossings and rejected reverse crossings, wide shortcuts and high-altitude skips; wave samples remained within bounds.
- Player input checks passed for acceleration, boost consumption, drift reward, hop, and pause freezing both the race clock and physics.
- The three-lap rule rejected an out-of-order gate, required the start crossing plus all three complete circuits, and opened results at the final crossing.
- Captured and reviewed fullscreen selection, race and pause layouts. The results screen was also captured and its visibility checked by the UI test.
- Rendered benchmark logs contain no script or renderer errors. Headless shutdown reports one `AudioStreamGeneratorPlayback` reference warning; rendered runs shut down cleanly. This is not a measured leak across races, but the headless shutdown path merits follow-up.

## Limits and next work

These results meet the prototype's numerical 60-average / 55-low target at both tested resolutions. They do not complete every production acceptance criterion: the course is a short blockout, these runs are not a fixed worst-case production replay, and the ten five-minute handling sessions and 30-minute rendered soak remain outstanding. No 1080p internal performance claim is made. Controller mappings are implemented; physical gamepad hardware has not been exercised.

The next work is player handling feedback, longer soak testing, better AI avoidance, a full rider animation pass, final water/shore effects, sound and track art. The remaining tracks, cups, items and cosmetics have not been implemented.

Run `tools/Benchmark-HydroDrift.ps1 -Quality 0` or `-Quality 1` from the repository root to repeat the GPU tests. Avoid running simultaneous GPU tests.
