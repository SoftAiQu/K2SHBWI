import json
import struct
import pytest
from src.core.format import CompressionType

SAMPLE = b'This is a small test payload for compression' * 10

@pytest.mark.parametrize('ctype', [CompressionType.NONE, CompressionType.ZLIB, CompressionType.LZMA, CompressionType.BROTLI, CompressionType.ZSTD])
def test_compressor_decompressor_roundtrip_or_skip(ctype):
    """Ensure compressor/decompressor roundtrip or skip if optional lib missing."""
    # Some compressors (brotli, zstandard) may not be installed in test env.
    try:
        comp = CompressionType.get_compressor(ctype)
        decomp = CompressionType.get_decompressor(ctype)
    except Exception as e:
        # If lib missing, we expect a CompressionError or ImportError - skip test
        pytest.skip(f"Skipping {ctype}: {e}")

    compressed = comp(SAMPLE)
    assert isinstance(compressed, (bytes, bytearray))

    decompressed = decomp(compressed)
    assert isinstance(decompressed, (bytes, bytearray))
    assert decompressed == SAMPLE
