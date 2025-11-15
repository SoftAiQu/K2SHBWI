import pytest

from src.algorithms.smart_compression import adaptive_compress, adaptive_decompress
from src.core.format_spec import CompressionType, CompressionError


def test_adaptive_compress_roundtrip_text():
    data = (b'This is a sample text data for compression. ' * 200)
    compressed, comp_type = adaptive_compress(data, data_type='text')
    assert isinstance(comp_type, CompressionType)
    # decompress via helper
    out = adaptive_decompress(compressed, comp_type)
    assert out == data


def test_adaptive_compress_roundtrip_binary():
    data = (b"\x00\x01\x02\x03" * 2000)
    compressed, comp_type = adaptive_compress(data, data_type='binary')
    assert isinstance(comp_type, CompressionType)
    out = adaptive_decompress(compressed, comp_type)
    assert out == data
