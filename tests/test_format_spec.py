import pytest
from src.core.format_spec import K2SHBWIMetadata, CompressionType


def test_metadata_pack_unpack_zlib():
    m = K2SHBWIMetadata()
    m.data.update({
        'title': 'T',
        'author': 'A',
        'created_date': '2025-10-29T00:00:00+00:00'
    })
    m.compression_type = CompressionType.ZLIB
    packed, length = m.pack()
    unpacked = K2SHBWIMetadata.unpack(packed)
    assert unpacked.data['title'] == 'T'
    assert unpacked.data['author'] == 'A'


@pytest.mark.parametrize('ctype', [CompressionType.BROTLI, CompressionType.LZMA, CompressionType.ZSTD])
def test_metadata_pack_unpack_optional(ctype):
    m = K2SHBWIMetadata()
    m.data.update({
        'title': 'T2',
        'author': 'A2',
        'created_date': '2025-10-29T00:00:00+00:00'
    })
    m.compression_type = ctype
    packed, length = m.pack()
    unpacked = K2SHBWIMetadata.unpack(packed)
    assert unpacked.data['title'] == 'T2'
    assert unpacked.data['author'] == 'A2'
