# Chunked Blender source

The knight roster is stored as 70 MB chunks to stay below GitHub's 100 MB file limit, without reducing geometry or rig detail.

Run `python tools/assemble_sources.py` from the repository root before opening `Hydro_Drift_Knights.blend`. Runtime setup does this automatically. SHA-256 verifies the reconstructed file and each chunk. The assembled `.blend` is ignored by Git.

After editing the roster in Blender, run `python tools/assemble_sources.py --pack` and commit the updated chunks and manifest. Never force-add the assembled file. Blender backup files (`.blend1`) are also ignored.
