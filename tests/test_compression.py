import pytest

from src.core.format_spec import CompressionType, CompressionError
from src.core.compression import compress_bytes, decompress_bytes


@pytest.mark.parametrize('ctype', [
    CompressionType.NONE,
    CompressionType.ZLIB,
    CompressionType.BROTLI,
    CompressionType.LZMA,
    CompressionType.ZSTD,
])
def test_compress_decompress_roundtrip(ctype):
    data = (b'K2SHBWI-test-' * 1000)
    try:
        comp = compress_bytes(ctype, data)
        out = decompress_bytes(ctype, comp)
        assert out == data
    except CompressionError as e:
        # Optional libraries may be missing (brotli, zstandard). Skip in that case.
        pytest.skip(f"Compression backend not available for {ctype.name}: {e}")
