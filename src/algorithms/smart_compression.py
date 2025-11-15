"""Smart compression helpers (Adaptive Hybrid Compression)

Adaptive-compression prototype. This module chooses a compression
algorithm using simple heuristics and compresses data using the
`CompressionType` helpers in the format spec. It returns the compressed
bytes and the chosen `CompressionType` enum instance. This keeps the
encoder/decoder compatible with the format's compression-type byte.
"""
from typing import Tuple
import zlib

from ..core.format import CompressionType
from ..core.errors import CompressionError


def _try_import(module_name: str):
    try:
        import importlib

        return importlib.import_module(module_name)
    except Exception:
        return None


def adaptive_compress(data: bytes, data_type: str = 'binary') -> Tuple[bytes, CompressionType]:
    """Select a compression algorithm heuristically and compress.

    Returns (compressed_bytes, CompressionType).
    Heuristics (simple):
      - If data looks textual (lots of printable ASCII), prefer Brotli if available.
      - If zstandard is available and data is large, prefer ZSTD.
      - Fall back to LZMA, then ZLIB.
    """
    # Heuristic: fraction of printable ASCII
    printable = sum(1 for b in data if 32 <= b <= 126)
    ratio = printable / max(1, len(data))

    # Check available backends
    brotli_mod = _try_import('brotli')
    zstd_mod = _try_import('zstandard')
    lzma_mod = _try_import('lzma')

    chosen: CompressionType = CompressionType.ZLIB

    # Prefer zstd for large data if available
    if zstd_mod and len(data) > 8_000:
        chosen = CompressionType.ZSTD
    # Prefer brotli for mostly-text data
    elif brotli_mod and ratio > 0.6:
        chosen = CompressionType.BROTLI
    # Prefer lzma for structured/binary JSON-like data if available
    elif lzma_mod and data_type in ('json', 'structured'):
        chosen = CompressionType.LZMA
    else:
        chosen = CompressionType.ZLIB

    # Use CompressionType helpers to get a compressor (will raise CompressionError if backend missing)
    try:
        compressor = CompressionType.get_compressor(chosen)
        compressed = compressor(data)
    except Exception as e:
        # On any failure, fallback to zlib
        try:
            compressor = CompressionType.get_compressor(CompressionType.ZLIB)
            compressed = compressor(data)
            chosen = CompressionType.ZLIB
        except Exception as e2:
            raise CompressionError(f'Adaptive compression failed: {e}; fallback also failed: {e2}')

    return compressed, chosen


def adaptive_decompress(data: bytes, comp_type: CompressionType) -> bytes:
    """Decompress using the provided CompressionType."""
    decompressor = CompressionType.get_decompressor(comp_type)
    return decompressor(data)
