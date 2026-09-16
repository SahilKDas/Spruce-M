# Hydro Drift character revision 2

Open `source/Hydro_Drift_Characters.blend` for the rebuilt cast. The main `Hydro_Drift_Library.blend` also contains these replacement collections.

## Modeling changes

- More adult proportions: smaller heads, longer thighs and shins, narrower wrists and ankles, shaped calves, shoulders and torsos.
- Continuous quad surfaces cross elbows and knees. Joint regions blend skin weights between the adjacent bones.
- Human riders have smaller inset eyes, eyelids, nose bridges, nostrils, lips, ears and modeled hair.
- Animal riders have species-specific snouts, gills, ears, tails or mantle shapes.
- Riding equipment includes fitted flotation panels, reflective tape, zippers, straps, seams, neoprene material detail, boot laces and soles.
- Each hand has a modeled palm, four fingers and a thumb. Fingers have knuckles and simple nail surfaces. **There are no finger or thumb bones.** All digit vertices follow the hand as a fixed shape.

## Rig controls

Each rider uses a single skinned character mesh with an Armature modifier. This replaces the previous rigid-part character construction.

Hide Presentation_V2 while editing, enable the rider's collection in the Outliner, select `NAME_Rig`, and enter Pose Mode.

- Torso: `pelvis`, `spine`, `chest`, `neck`, `head`.
- Arms: `clavicle.L/R`, `upper_arm.L/R`, `forearm.L/R`, `hand.L/R`.
- Legs: `thigh.L/R`, `shin.L/R`, `foot.L/R`.
- Placement: `root`.
- Optional IK targets: `CTRL_hand.L/R`, `CTRL_foot.L/R`; pole controls: `CTRL_elbow.L/R`, `CTRL_knee.L/R`.

FK (rotating bones directly) is the default. To use an IK chain, select its forearm or shin and set the `Optional IK` constraint influence to 1, then move its matching target and pole controls. IK constraints are baked into exported animations rather than exported as Blender constraints.

Timeline frames 1–20 show the neutral pose; 40–80 demonstrate elbow and knee flexion; 100 returns to neutral. The test demonstrates articulation and is not a finished racing animation.

## Exports and validation

The existing `exports/NAME.glb`, `NAME_LOD1.glb`, and `NAME_LOD2.glb` files are replaced by the revision 2 skinned versions. Each includes a skeleton and skin weights. The main GLB includes the joint-bend animation; LOD meshes share that animation instead of storing duplicate clips. `character_validation.json` checks the complete roster's weight normalization, required limb bones, absence of finger bones, exported skin attributes and LOD triangle reduction.

## Rebuild order

1. Run `rebuild_characters.py` using Blender in background mode.
2. Run `validate_characters_v2.py`.
3. Run `integrate_characters_v2.py` to update the general asset library.
4. Run `validate_assets.py` to refresh the global export/storage report.

The old `build_assets.py` and `rig_riders.py` reproduce revision 1 characters. If you rebuild that base library, run these revision 2 steps afterward. Course and watercraft assets have not been redesigned by this revision.

