"""Reject staged blobs above a conservative 100,000,000-byte GitHub limit."""
import subprocess
import sys

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
sys.exit(bool(oversized))
