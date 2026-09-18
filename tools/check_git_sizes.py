"""Reject staged blobs above a conservative 100,000,000-byte GitHub limit."""
import subprocess
import sys
from pathlib import Path

entries = subprocess.check_output(['git', 'ls-files', '--stage', '-z']).split(b'\0')
oversized = []
for entry in entries:
    if not entry:
        continue
    metadata, path = entry.split(b'\t', 1)
    blob = metadata.split()[1].decode()
    size = int(subprocess.check_output(['git', 'cat-file', '-s', blob]))
    if size > 100_000_000:
        oversized.append((path.decode('utf-8'), size))
for path, size in oversized:
    print(f'File exceeds 100 MB: {path} ({size:,} bytes). Split or compress before committing.')
root = Path(__file__).resolve().parents[1]
folder_bytes = sum(path.stat().st_size for path in root.rglob('*') if path.is_file())
if folder_bytes >= 10_000_000_000:
    print(f'Project folder exceeds the 10 GB budget: {folder_bytes:,} bytes, including Git and local tools.')
sys.exit(bool(oversized) or folder_bytes >= 10_000_000_000)
