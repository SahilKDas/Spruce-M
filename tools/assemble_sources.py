"""Reassemble chunked Blender sources, verifying every byte with SHA-256."""
import hashlib
import json
from pathlib import Path


def assemble():
    source = Path(__file__).resolve().parents[1] / 'assets' / 'source'
    for manifest in source.glob('*.parts.json'):
        info = json.loads(manifest.read_text())
        target = source / info['file']
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == info['sha256']:
            continue
        data = bytearray()
        for part in info['parts']:
            chunk = (source / part['file']).read_bytes()
            if len(chunk) != part['bytes'] or hashlib.sha256(chunk).hexdigest() != part['sha256']:
                raise ValueError(f"Corrupt source chunk: {part['file']}")
            data.extend(chunk)
        if len(data) != info['bytes'] or hashlib.sha256(data).hexdigest() != info['sha256']:
            raise ValueError(f'Corrupt assembled source: {target}')
        temporary = target.with_suffix('.assembling')
        temporary.write_bytes(data)
        temporary.replace(target)
        print(f'Reassembled {target.name}: {len(data)} bytes')


def pack():
    source = Path(__file__).resolve().parents[1] / 'assets' / 'source'
    for manifest in source.glob('*.parts.json'):
        info = json.loads(manifest.read_text())
        target = source / info['file']
        data = target.read_bytes()
        parts = []
        for index, start in enumerate(range(0, len(data), 70_000_000), 1):
            chunk = data[start:start + 70_000_000]
            name = target.name + f'.part{index:02d}'
            (source / name).write_bytes(chunk)
            parts.append(dict(file=name, bytes=len(chunk), sha256=hashlib.sha256(chunk).hexdigest()))
        manifest.write_text(json.dumps(dict(file=target.name, bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(), parts=parts), indent=2) + '\n')


if __name__ == '__main__':
    import sys
    pack() if '--pack' in sys.argv else assemble()
