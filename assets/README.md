# Hydro Drift — Blender asset library

Character revision 2 replaces the original riders with anatomically proportioned, skinned characters. See `CHARACTER_RIGS.md` and open `source/Hydro_Drift_Characters.blend`. Rebuild revision 2 after any use of the legacy base-generation scripts.

Original procedural models authored in Blender 5.1.2 for this project. No downloaded models, texture packs, or external linked resources are required.

## Open the files

- `source/Hydro_Drift_Library.blend`: editable characters, watercraft, scenery, race props and presentation lighting. Individual models are collections. Source collections are excluded from the presentation view layer; enable a collection in the Outliner to edit it.
- `source/Hydro_Drift_Courses.blend`: six assembled course art layouts. Sunbeam Lagoon is visible by default. Toggle collection visibility to inspect another layout.
- `exports/`: individual binary glTF files, two reduced-detail versions of every individual asset, and six course layout exports.
- `previews/`: Blender-rendered model sheets and course overviews.
- `manifest.json`: asset inventory and evaluated triangle counts.
- `validation.json`: export structure, geometry counts, animation counts and storage audit.
- `course_layouts.json`: ordered reference race-line points and checkpoint counts.

## Inventory

8 riders: Kai, Zuri, Riptide, Pip, Marina, Bolt, Mochi, Ink.

3 watercraft: Needle (agile), Surge (balanced), Leviathan (power).

25 other assets: palm, coastal rocks, ice cluster, dock, buoy, start arch, ramp, direction sign, shipping container, harbor building, mangrove, ruins arch, iceberg, lighthouse, volcano, geyser vent, boat, umbrella, barrier, four pickups, trophy, and water tile.

6 assembled course art layouts: Sunbeam Lagoon, Neon Harbor, Mangrove Rush, Glacier Run, Stormbreak Bay, Ember Atoll. These share a reference loop for early art evaluation; distinct final racing geometry must be designed and playtested.

## Asset conventions

- Blender source uses meters, Z up, forward -Y. glTF exports use the standard glTF axis conversion.
- Main assets sit near their local origin. Craft have named rider, handlebar, and wake markers.
- Base exports are the highest runtime detail; `_LOD1` and `_LOD2` are progressively reduced. Engine import does not automatically configure LOD switching. Small parts are retained to protect silhouettes.
- Revision 2 riders use shared PBR colors and a small embedded woven normal map. Scenery and watercraft retain solid PBR colors. Surface UVs are provided on the main rider forms; dedicated painted texture atlases and lightmap unwraps are not included.
- Curved character surfaces are smooth polygon meshes; watercraft hulls retain editable subdivision modifiers in Blender. This is a stylized foundational art pack, not finished hand-sculpted cinematic art.
- Revision 2 characters have 28-bone rigs including optional IK controls, a skinned mesh with weighted elbows and knees, and a 100-frame joint-bend test. Fingers are modeled but have no individual bones; they remain fixed to each hand. See CHARACTER_RIGS.md for controls. Final racing clips and facial animation are not included.
- Course checkpoint empties and a reference curve are authoring aids. No racing logic, collision setup, AI, water simulation, buoyancy, audio or engine effects are implemented here.
- The water mesh and course water planes are visual placeholders. Engine water needs continuous waves, reflection settings and wake effects. Blender presentation lighting is not a gameplay performance benchmark.

## Storage and performance budget

Persistent project budget: **10,000,000,000 bytes** (10 GB decimal), including source assets, exports, previews and future game files. Temporary build files may be excluded, as requested. Do not fill the budget unnecessarily.

Target machine: i7-1255U, NVIDIA MX550 2 GB VRAM, approximately 16 GB RAM, 1920×1080 display. Runtime FPS has not been measured: no playable engine build exists yet. Start performance testing at 1280×720 and tune toward 60 FPS. Import only one detail level at a time for distant props; use instancing for repeated track scenery; combine compatible render parts when preparing final runtime characters.

## Rebuild

From the project root, using PowerShell:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe' --background --python assets/build_assets.py
& 'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe' --background --python assets/rig_riders.py
& 'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe' --background --python assets/build_courses.py
& 'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe' --background --python assets/validate_assets.py
```

The build writes the same named outputs. Blender may retain `.blend1` backup files. Rendering uses CPU Cycles so this asset-generation step does not depend on GPU render support. All generated geometry and material definitions are editable in the source script and saved Blender files.



