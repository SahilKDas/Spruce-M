# Hydro Drift — knight roster and high-detail watercraft

The active cast is now **eight armored knights**. The character rebuild uses an anatomical base with sculpted multiresolution detail, fitted metal armor, a closed helmet, gauntlets, and armored boots. Bodies have natural shoulders, elbows, hands, hips, and knees. Each knight has a distinct build, enamel palette, and helmet crest.

## Current editable sources

- [Knight roster](source/Hydro_Drift_Knights.blend): all eight characters and their 20-bone body rigs.
- [Kai authoring source](source/Hydro_Drift_Knight_Kai.blend): the base knight's editable armor and anatomical mesh.
- [Watercraft](source/Hydro_Drift_Watercraft_v3.blend): Needle, Surge, and Leviathan, with continuous shaped hulls, footwell tread, upholstered saddles, controls, and waterjets.
- [Environment](source/Hydro_Drift_Environment_v3.blend): palm, rocks, buoy, ramp, dock, umbrella, and Sunbeam island terrain.
- [Knight roster preview](previews/25_knight_roster.png) and [actual exported riding pose](previews/26_knight_riding_pose.png).

The neutral knight GLBs contain approximately **1.72 million triangles each**. The Blender body retains its additional sculpted multiresolution level. Watercraft have approximately **515k source triangles**. These counts describe geometry density; visual review of shape, materials, armor fit, and deformation is still required.

The anatomical mesh comes from Blender's official CC0 human base-mesh bundle. Hydro Drift's armor, helmets, materials, skeleton, weights, and export pipeline are custom work. See [source credit and license](vendor/README.md). This replaces the earlier mannequin construction; the anatomical base is not claimed as original project modeling.

## Knight roster

| Name | Armor identity |
| --- | --- |
| Kai | Sun Knight — orange and teal |
| Zuri | Tide Knight — teal and pale steel |
| Riptide | Deepwater Knight — blue with a high fin crest |
| Pip | Copper Scout — smaller copper armor |
| Marina | Rose Knight — rose enamel and paired crests |
| Bolt | Iron Knight — broad gunmetal armor |
| Mochi | Bronze Guardian — broad cream and bronze armor |
| Ink | Violet Knight — purple armor and split crest |

## Runtime art

Generated `game/art` is ignored by Git and recreated by setup. The local knight targets **160k triangles**, opponents **22k**, before Godot distance LODs. Craft use 120k local / 40k opponent meshes. Repeated buoys use 2k meshes in a MultiMesh. Full-detail sources and reusable GLBs stay available in `assets/source` and `assets/exports`.

Each hand and its modeled fingers move together; **there are no finger or thumb bones**. Plate pieces use rigid limb weights. The exporter solves the seated pose geometrically and bakes a static `Riding` action. Full racing, trick, and victory animations remain future work. See [rig instructions](CHARACTER_RIGS.md).

Blender uses meters, Z up, forward -Y. Standard GLB export performs the coordinate conversion for Godot. Shared PBR materials define the colors and metal finishes. The Blender look-development materials include procedural microdetail; dedicated baked production texture atlases remain future work.

## Rebuild

To prepare the game from committed sources:

```powershell
./tools/Setup-HydroDrift.ps1
```

To rebuild the knight authoring files and exports:

```powershell
$blender = 'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe'
& $blender --background --python-exit-code 1 --python assets/rebuild_knight_kai.py -- --no-render
& $blender --background --python-exit-code 1 --python assets/build_knight_roster.py
& $blender --background --python-exit-code 1 --python assets/audit_knight_sources.py
& $blender --background --python-exit-code 1 --python assets/export_knights.py
python assets/validate_knights.py
& $blender --background --python-exit-code 1 --python assets/render_knight_riding.py
```

The committed `vendor/Blender_CC0_Male_Anatomy.blend` makes the character build self-contained. Exporting all eight dense models takes several minutes. Most source viewport subdivision is disabled to keep editing responsive; render detail is retained.

Rebuild watercraft/environment with `rebuild_watercraft_v3.py` and `rebuild_environment_v3.py`, then run `export_assets_v3.py -- --props-only` through Blender. `tools/prepare_runtime_assets.py` exports these props and then the current knights.

## Validation and scope

- [Source rig audit](knight_source_validation.json): 20 body bones, no finger bones, rigid digit and armor weights.
- [Export audit](knight_validation.json): evaluated geometry and normalized skinning.
- [Actual GLB audit](knight_glb_validation.json): triangle counts, finite bounds, limb bones, actual weight values, and riding animation channels.
- [Hardware performance and game tests](../benchmarks/README.md).

The earlier unversioned libraries, revision 2/3 character files, their previews, and old validation reports are historical studies. They are not the active game cast. Future-course props and six earlier course layouts have not been redesigned in this pass and are not loaded by the playable course.

Persistent storage must remain below **10 GB**. Target hardware remains the i7-1255U, MX550 2 GB, and 16 GB RAM. The game retains 16:9 fullscreen and its 60 FPS cap.
