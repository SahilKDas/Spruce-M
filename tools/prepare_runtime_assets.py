"""Prepare the current high-detail Hydro Drift art in Blender background mode."""
import runpy,sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / 'tools/assemble_sources.py'), run_name='__main__')
for filename in ('Hydro_Drift_Knights.blend','Hydro_Drift_Watercraft_v3.blend','Hydro_Drift_Environment_v3.blend'):
    source = ROOT / 'assets/source' / filename
    if not source.is_file():
        raise FileNotFoundError(f'Missing active source: {source}')
sys.argv.append('--props-only')
runpy.run_path(str(ROOT / 'assets/export_assets_v3.py'), run_name='__main__')
sys.argv.remove('--props-only')
runpy.run_path(str(ROOT / 'assets/export_knights.py'), run_name='__main__')
