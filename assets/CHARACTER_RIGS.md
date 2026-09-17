# Hydro Drift knight rigs

Open [Hydro_Drift_Knights.blend](source/Hydro_Drift_Knights.blend). All eight knights use the anatomical mesh and fitted armor. Select `NAME_Rig` and enter Pose Mode.

## Bones

Each source rig has 20 bones:

- `root`, `pelvis`, `spine`, `chest`, `neck`, `head`.
- `clavicle.L/R`, `upper_arm.L/R`, `forearm.L/R`, `hand.L/R`.
- `thigh.L/R`, `shin.L/R`, `foot.L/R`.

Rotate these bones directly for FK posing. The body blends across joints. Helmets, gauntlets, boots, and individual armor plates retain rigid attachment weights. **Fingers have modeled anatomy but no individual bones or animation.** Every digit follows its hand.

`audit_knight_sources.py` checks actual hand and plate vertices against their required bones. This includes a regression check for fingertips accidentally following leg bones. `validate_knights.py` checks the exported binary skin weights and required limb bones.

## Riding pose

`export_knights.py` positions the pelvis over the saddle, leans the spine and chest, and solves both arms and legs with a two-bone geometric calculation. It fixes the wrist/foot orientations and bakes the pose into the two-frame `Riding` action. No runtime IK solver is required. The game adds whole-rider lean.

Neutral high-detail/LOD GLBs go to `assets/exports`; posed near/far GLBs go to ignored `game/art`. Near/far budgets are 160k / 22k triangles. Full racing, jump, trick, and victory animation clips remain outstanding.

The source anatomical body retains sculpted Multires detail. Enable its viewport levels for detailed editing; the roster stores reduced viewport levels to control memory. The exporter evaluates body level 2 while preserving the higher sculpt level in the Blender source.
