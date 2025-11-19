"""Small benchmark script to compare compression backends on sample assets.

This script is meant to be run manually (it's not a unit test). It will
measure compressed size and compression time for available backends.

Now with real-time logging support:
  - Metrics logged to /logs/benchmark_results/
  - JSON, TXT, and hash files generated
  - Enable with --log flag or log=True parameter
"""
import time
from pathlib import Path
import json
import sys

from src.core.compression import compress_bytes
from src.core.format_spec import CompressionType
from src.utils.test_logger import TestLogger

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


def bench(enable_logging=False):
    """
    Run compression benchmarks.
    
    Args:
        enable_logging: If True, generate timestamped logs in /logs/benchmark_results/
    """
    results = {}
    
    # Initialize logger if enabled
    logger = None
    if enable_logging:
        logger = TestLogger("benchmark_compression", log_type="benchmark")
    
    for name, path in ASSETS.items():
        data = _read_bytes(path)
        if not data:
            print(f"Asset missing: {path}; skipping {name}")
            continue
        
        results[name] = {}
        original_size = len(data)
        
        for ctype in TYPES:
            try:
                t0 = time.perf_counter()
                out = compress_bytes(ctype, data)
                t1 = time.perf_counter()
                
                compressed_size = len(out)
                elapsed_ms = (t1 - t0) * 1000
                
                results[name][ctype.name] = {
                    'compressed': compressed_size,
                    'time_ms': elapsed_ms
                }
                
                # Log if enabled
                if logger:
                    logger.log_compression_metric(
                        file_name=f"{name}",
                        original_bytes=original_size,
                        compressed_bytes=compressed_size,
                        algorithm=ctype.name,
                        processing_time_ms=elapsed_ms,
                        status="SUCCESS"
                    )
                
                # Print to console
                ratio = ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0
                print(f"  {ctype.name:8s}: {compressed_size:5d} bytes ({ratio:6.2f}%) in {elapsed_ms:8.2f}ms")
                
            except Exception as e:
                results[name][ctype.name] = {'error': str(e)}
                
                # Log error if enabled
                if logger:
                    logger.log_compression_metric(
                        file_name=f"{name}",
                        original_bytes=original_size,
                        compressed_bytes=0,
                        algorithm=ctype.name,
                        processing_time_ms=0,
                        status="FAIL",
                        error_msg=str(e)
                    )
                
                print(f"  {ctype.name:8s}: ERROR - {e}")
        
        print()
    
    # Save logs if enabled
    if logger:
        logger.add_summary({
            "asset_count": len([p for p in ASSETS.values() if _read_bytes(p)]),
            "algorithm_count": len(TYPES),
            "benchmark_type": "compression_ratio_and_speed"
        })
        paths = logger.save_log()
        print("=" * 80)
        print("LOGGING RESULTS:")
        print(f"✅ JSON Log: {paths['json']}")
        print(f"✅ TXT Report: {paths['txt']}")
        print(f"✅ Hash File: {paths['hash']}")
        print("=" * 80)
        print()
    
    return results


if __name__ == '__main__':
    # Check for --log flag
    enable_logging = '--log' in sys.argv or 'log=True' in sys.argv
    
    print("Compression Algorithm Benchmark")
    print("=" * 80)
    print("Testing: ZLIB, BROTLI, LZMA, ZSTD")
    print()
    
    for name, path in ASSETS.items():
        print(f"Asset: {name} ({path.name})")
    print()
    
    if enable_logging:
        print("📊 LOGGING ENABLED - Results will be saved to /logs/benchmark_results/")
        print()
    
    results = bench(enable_logging=enable_logging)
    
    print("\nSummary (JSON format):")
    print(json.dumps(results, indent=2))
