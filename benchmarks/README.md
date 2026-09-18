# September 18 Godot update

The latest 45-second native 1920×1080 fullscreen run (10-second warm-up excluded) averaged **60.00 FPS**, with **54.81 FPS 1% low**, on the MX550. It uses 2× MSAA and the 60 FPS cap. See `performance_1080p.json`. This short run does not establish sustained performance or eliminate all possible stalls.

The updated handling passed 20 automated races, controls, ordered checkpoints, three-lap completion, interpolation/recovery, and exit confirmation/cancellation checks. Rendered pause and confirmation screens were inspected. An existing ObjectDB shutdown warning remains in headless tests.

## Historical checkpoint

# Hydro Drift — pre-Unity checkpoint validation

Measured September 16, 2026 on the NVIDIA GeForce MX550, Godot 4.7 Mobile/Vulkan renderer, with eight revision-4 armored knights. This preserves the Godot prototype before the user-requested Unity migration. The user rejected its handling and visual quality; passing functional checks does not establish acceptable game feel.

## Latest rendered run

| Measurement | Performance preset |
| --- | ---: |
| Output | 1920 × 1080 fullscreen, 16:9 |
| Internal 3D resolution | 1280 × 720 |
| FPS cap | 60 |
| Duration / excluded warm-up | 90 / 10 seconds |
| Average FPS | 58.60 |
| 1% low FPS | 20.62 |
| Peak draw calls | 116 |
| Peak rendered primitives | 1,119,066 |
| Peak renderer allocations | 148.7 MiB |
| Automatic recoveries | 3 |

[Raw revision-4 results](performance_720p.json). This run **does not meet** the stable 60 FPS / 55 FPS 1%-low acceptance target. It includes a 752 ms frame stall and repeated slower sections. Their exact cause has not been isolated. The cap remains enabled; it is not a performance guarantee.

The retained [900p result](performance_900p.json) is from the earlier prototype and does **not** measure the knight assets. No revision-4 900p or 1080p claim is made.

Frame intervals use the wall clock. The 1% low is the inverse of the average duration of the slowest 1% of sampled frames. Screenshot capture occurs during warm-up. Renderer allocations exclude driver, desktop, and other application allocations; they are not total dedicated VRAM use. Blender rendering was complete before this GPU run.

## Functional and asset checks

- All eight knight imports passed; actual GLB weights are normalized, finite, and contain no finger bones. Each source has 20 body bones. Source checks verified rigid hand and armor attachments.
- [20 automated one-lap, eight-racer races completed](integration.json), with menu flow, pause, checkpoint-preserving recovery, results, and time-trial checks.
- Ordered gates reject reverse crossings, shortcuts, and high-altitude skips.
- Throttle, boost consumption, drift reward, hop, and paused physics/time checks passed.
- Three-lap completion and out-of-order gate rejection passed.
- Actual fullscreen menu, racing, pause, and results images were captured. The menu and racing views were inspected after the final hand-pose correction.
- Rendered runs contain no script/renderer errors. Headless shutdown still reports one ObjectDB/AudioStreamGeneratorPlayback reference warning.

## Remaining limits

The course is a short prototype. Production track art, water effects, final materials, full rider animations, AI tactics, sound, longer handling sessions, and a 30-minute rendered soak remain incomplete. Physical gamepad hardware has not been tested. The Unity version needs fresh functional and hardware benchmarks; these Godot results cannot be transferred to it.

Repeat the historical Godot benchmark with `tools/Benchmark-HydroDrift.ps1 -Quality 0`.
