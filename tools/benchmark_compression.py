"""Small benchmark script to compare compression backends on sample assets.

This script is meant to be run manually (it's not a unit test). It will
measure compressed size and compression time for available backends.
"""
import time
from pathlib import Path
import json

from src.core.compression import compress_bytes
from src.core.format_spec import CompressionType

ASSETS = {
    'image': Path(__file__).parent.parent / 'tests' / 'assets' / 'sample.png',
    'metadata': Path(__file__).parent.parent / 'tests' / 'assets' / 'metadata.json',
    'hotspots': Path(__file__).parent.parent / 'tests' / 'assets' / 'hotspots.json',
}

TYPES = [CompressionType.ZLIB, CompressionType.BROTLI, CompressionType.LZMA, CompressionType.ZSTD]


def _read_bytes(p: Path) -> bytes:
    if not p.exists():
        return b''
    if p.suffix.lower() in ('.json', '.txt'):
        return p.read_text(encoding='utf-8').encode('utf-8')
    return p.read_bytes()


def bench():
    results = {}
    for name, path in ASSETS.items():
        data = _read_bytes(path)
        if not data:
            print(f"Asset missing: {path}; skipping {name}")
            continue
        results[name] = {}
        for ctype in TYPES:
            try:
                t0 = time.perf_counter()
                out = compress_bytes(ctype, data)
                t1 = time.perf_counter()
                results[name][ctype.name] = {'compressed': len(out), 'time_ms': (t1-t0)*1000}
            except Exception as e:
                results[name][ctype.name] = {'error': str(e)}
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    bench()
