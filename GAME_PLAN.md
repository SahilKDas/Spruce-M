# Hydro Drift — production plan

## Product target

Hydro Drift is a third-person arcade racing game for Windows. Eight distinct riders race personal watercraft across bright coastal courses. The handling should be readable and responsive: carve, drift, jump, land, ride wakes, earn boost, and use a small set of items.

The first release target is this computer:

| Component | Target hardware |
| --- | --- |
| CPU | Intel Core i7-1255U, 10 cores / 12 threads |
| GPU | NVIDIA GeForce MX550, 2 GB dedicated VRAM |
| Memory | 16 GB |
| Display | 1920 × 1080 |
| Persistent project storage | 10 GB maximum |

Primary performance target: a stable 60 FPS during an eight-racer match. Begin at 1280 × 720 internal resolution and test 1600 × 900 after the frame-time target is met. Offer a 30 FPS quality mode at 1920 × 1080 only if it remains stable.

## Technical direction

Use Godot 4 with GDScript and the Mobile renderer for the first playable build. It accepts the existing GLB exports, has a smaller production footprint than a heavyweight engine, and preserves access to modern rendering APIs. Maintain Compatibility as a fallback experiment only if driver or frame-time testing justifies it.

Repository layout:

```text
assets/             Blender sources, exports, previews and validation
game/               Godot project
game/scenes/        races, menus, riders, craft and track scenes
game/scripts/       gameplay code
game/materials/     runtime shaders and materials
game/audio/         compressed music and sound effects
game/data/          rider, craft, item and cup resources
builds/             ignored local Windows builds
benchmarks/         repeatable performance captures and reports
```

Use Git LFS before the repository grows substantially if it will be pushed to a remote. `.blend`, `.glb`, `.png`, and audio files are binary and do not produce useful textual diffs.

## Performance budgets

The GPU's 2 GB VRAM is the limiting resource. These are initial budgets, to be revised from measurements on the target machine.

| System | Budget |
| --- | --- |
| Total frame | 16.67 ms at 60 FPS |
| Game logic and physics | 4 ms CPU |
| Rendering submission | 4 ms CPU |
| GPU rendering | 14 ms typical, 16 ms worst sustained section |
| Game VRAM use | 1.55 GB target, 1.75 GB hard warning |
| Process RAM | 6 GB target, 8 GB warning |
| Installed game | 4 GB initial release target |
| Whole working repository | 10 GB hard limit excluding temporary files |
| Draw calls | 800 typical, 1,200 maximum in busiest race view |
| Visible triangles | 1.5 million typical, 2.5 million maximum |
| Transparent particles | 25,000 visible maximum, aggressively pooled |
| Active rigid bodies | 32 maximum; scenery uses static collision |

Runtime character targets per racer:

| Distance | Triangle target | Texture target |
| --- | --- | --- |
| Local rider close-up | 70k–100k | shared 2K body atlas, 1K gear atlas |
| Nearby opponent | 25k–45k | 1K atlases |
| Mid-distance opponent | 8k–15k | 512–1K atlases |
| Far opponent | 2k–5k or impostor | 256–512 atlas |

The current Kai and Zuri source meshes are about 187k–188k triangles, and their current LOD2 exports are about 47k. Treat the full meshes as Blender source art. Produce additional game LODs before eight-racer performance testing. Other riders are about 78k–80k at full detail and 19k–20k at LOD2, which is closer to the nearby-opponent budget.

Texture rules:

- Prefer shared 1K atlases and trim sheets. Reserve 2K maps for the selected local rider or hero craft.
- Use BC-compressed textures in the Windows build; avoid uncompressed normal maps.
- Keep scenery texel density consistent and reuse materials across track modules.
- Avoid 4K textures on this hardware.
- Load only the current course, its racers, and shared UI/audio. Release previous race resources between events.

## Core game architecture

### Watercraft controller

Build the craft as an arcade controller rather than a fully simulated boat.

- One rigid body per craft.
- Four water sample points: bow, stern, port and starboard.
- Apply spring-damper buoyancy at each point against an analytic wave-height function.
- Apply forward thrust along the water tangent, lateral grip opposing sideways velocity, yaw torque from steering, and drag based on speed.
- Reduce lateral grip while drifting. Rider lean adds yaw authority and moves the visual body without changing collision unpredictably.
- Use a simplified convex hull for collision. Never use rendered mesh collision on racers.
- Run gameplay physics at 60 Hz. Visual water may contain extra small waves that do not affect physics.

Initial handling values must live in editable resources: acceleration, top speed, reverse speed, steering curve, drift grip, boost force, air control, buoyancy spring, damping, landing forgiveness and recovery timing.

### Water rendering

Use one low-density tiled water mesh centered around the camera with vertex displacement from two or three analytic wave layers. Calculate the same large-wave function in gameplay code for buoyancy.

- One opaque or near-opaque water material; avoid expensive multilayer transparency.
- Screen-space color/depth sampling for shallow refraction only on Medium and High.
- One reflection probe or low-resolution planar reflection for selected showcase areas. Disable planar reflections on Low.
- Foam is a pooled particle ribbon and decal system driven by craft speed and slip angle.
- Each racer gets one primary wake ribbon. Distant wakes reduce update frequency and particle density.
- Shore foam uses animated masks, not fluid simulation.

### Camera and controls

- Controller-first input with keyboard support.
- Speed-based camera distance and field of view.
- Predictive look into turns and toward upcoming checkpoints.
- Brief landing impulse and drift shake, with independent strength settings and an option to disable shake.
- Camera collision prevents scenery clipping without sudden zoom changes.

### Racing systems

- Ordered checkpoint gates validate progress; lap counting requires the full gate sequence.
- Position uses lap, checkpoint index, and distance along the course reference spline.
- Respawn uses the last valid checkpoint, aligned to the spline and checked for overlap.
- Boost meter rewards drift duration, clean landings, tricks and wake riding.
- First item set: boost battery, bubble shield, wake pulse and whirlpool trap.
- Rubber-banding changes AI tactical choices and minor acceleration limits; it never teleports racers or ignores collisions.

### AI

- Drive toward sampled points on a racing spline with separate speed and steering targets.
- Author alternate splines for shortcuts and passing lanes.
- Use raycasts for local avoidance of racers, hazards and track edges.
- AI difficulty changes look-ahead distance, reaction delay, drift confidence, item timing and recovery error.
- Run strategic updates at 10 Hz and steering/physics at 60 Hz. Stagger strategic updates across racers.

## Content scope

### Vertical slice

- Kai and Zuri playable; Riptide and Pip as AI opponents.
- Needle and Surge craft.
- Sunbeam Lagoon with one complete two-minute lap.
- Four-racer race, time trial, character select, results screen and restart.
- Drift boost, wake riding, one jump route and boost battery pickup.
- Finished controller vibration, engine pitch, wake audio, UI feedback and accessibility settings.

### First complete game

- Eight riders and three craft classes.
- Six distinct tracks: Sunbeam Lagoon, Neon Harbor, Mangrove Rush, Glacier Run, Stormbreak Bay and Ember Atoll.
- Three cups, single race and time trial.
- Eight-racer AI matches.
- Four item types and cosmetic color unlocks.
- Local profile saving and configurable controls.

Online multiplayer and split-screen are outside the initial release. Split-screen would multiply rendering cost and should only enter scope after a two-camera benchmark passes on the MX550.

## Milestones and acceptance tests

### 0. Repository and asset preparation

- Track all existing assets and documentation.
- Create the Godot project, input map and project directory structure.
- Import one rider and one craft with correct scale, animation and materials.
- Retopologize or generate game-ready LODs for Kai and Zuri.
- Establish repeatable benchmark commands and a debug overlay for FPS, CPU/GPU frame time, draw calls, triangles, RAM and VRAM.

Done when an empty benchmark scene launches on the MX550, records metrics, and contains no missing-resource errors.

### 1. Gray-box handling prototype

- Flat test lake, buoy slalom, jump ramp and recovery zone.
- One craft controller with buoyancy, steering, drift, boost, jump and respawn.
- Chase camera and controller/keyboard input.

Done when ten consecutive five-minute sessions have no loss of control, no flipped-craft soft lock and no checkpoint or respawn failure. Target 120 FPS in the simple test scene, leaving headroom for final art.

### 2. Complete race loop

- Sunbeam Lagoon blockout, checkpoint and lap logic, four AI racers, countdown, HUD and results.
- Position tracking, item pickup, audio placeholders and pause/settings menus.

Done when 20 automated or observed races finish correctly and four racers hold 60 FPS at 1600 × 900 internal resolution in the blockout.

### 3. Visual benchmark

- Final-style local rider and craft, eight visible racers, water, wakes, spray, island scenery and lighting.
- Low, Medium and High presets.
- Shader/material warm-up during track loading.

Done when the busiest 90-second replay holds a 1% low of at least 55 FPS and an average of at least 60 FPS at the chosen default resolution, VRAM stays below 1.75 GB, and there are no visible shader-compilation hitches after loading.

If the test fails, reduce in this order: wake particles, reflection resolution, shadow distance, opponent LOD distance, water refraction, scenery visibility ranges, then internal resolution. Do not lower control or physics update rate.

### 4. Vertical slice

- Finish the defined vertical-slice content.
- Replace placeholders, tune handling and AI, perform input/accessibility pass, and package a Windows build.

Done when a new player can launch, select a rider, complete a race, understand drifting and restart without developer assistance; the build completes a 30-minute soak test without sustained frame-time degradation.

### 5. Production content

- Complete eight riders, three craft classes, six tracks, cups, items and cosmetics.
- Profile every course with eight racers after each art pass.
- Keep course-specific assets within a defined bundle so only one course remains resident.

Done when every track meets the visual benchmark and all championship progress saves and restores correctly.

### 6. Release preparation

- Quality presets, first-run hardware detection, controller remapping, save migration, crash logging and credits.
- Full packaged-build tests at 720p, 900p and 1080p.
- Verify clean install size, storage usage and offline operation.

Done when the default preset selected on the target computer produces stable play without manual graphics tuning.

## Graphics presets

| Setting | Low | Medium (target default) | High |
| --- | --- | --- | --- |
| Internal resolution | 1280 × 720 | 1600 × 900 | 1920 × 1080 |
| Shadows | one sun, short distance | one sun, medium distance | longer distance |
| Reflection | probes only | probes + selective SSR | low-resolution planar where budget permits |
| Water refraction | off | shallow/simple | full local effect |
| Wake particles | 35% | 65% | 100% |
| Opponent detail | earlier LOD | standard LOD | later LOD |
| Scenery density | reduced | standard | standard with longer range |
| Post effects | color grade | color grade + subtle bloom | adds selective effects |

Use dynamic resolution only as a guarded fallback, with a floor of 67% and a slow response to prevent visible pumping. The Medium preset should pass without relying on frequent resolution changes.

## Storage allocation

| Category | Maximum |
| --- | --- |
| Blender source and working art | 3.0 GB |
| Runtime meshes and textures | 2.0 GB |
| Audio | 1.0 GB |
| Godot source, cache metadata and scripts | 0.75 GB |
| Local packaged builds | 1.5 GB |
| Tests, benchmarks and previews | 0.75 GB |
| Reserved headroom | 1.0 GB |

Generated import caches and temporary render files should live outside the persistent budget where practical. Keep one current packaged build; archive or remove obsolete local builds after verifying the replacement.

## Immediate implementation order

1. Initialize `game/` as a Godot Mobile project and configure inputs and quality settings.
2. Build a benchmark lake and metric overlay.
3. Import Kai and Needle, validate scale, skeleton, animation and material count.
4. Create lower runtime LODs for Kai and Zuri; merge materials into small atlases.
5. Implement analytic waves and the four-point buoyancy craft controller.
6. Add drift, boost, jump, recovery and chase camera.
7. Build Sunbeam Lagoon as a gray-box course and add checkpoints.
8. Add four AI racers and run the first target-machine performance capture.
9. Revise budgets from measured bottlenecks before producing final course art.

The next engineering deliverable should be the gray-box handling benchmark. It decides whether 900p/60 is achievable and prevents the project from accumulating expensive art before the core racing feel and performance target are proven.
