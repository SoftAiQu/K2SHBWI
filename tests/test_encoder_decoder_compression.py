import json
import os
from pathlib import Path
import tempfile
import pytest

from src.core.encoder import K2SHBWIEncoder
from src.core.decoder import K2SHBWIDecoder
from src.core.format_spec import CompressionType

ASSETS_DIR = Path(__file__).parent / 'assets'
SAMPLE_IMAGE = ASSETS_DIR / 'sample.png'

@pytest.mark.parametrize('comp_types', [
    (CompressionType.ZLIB, CompressionType.ZLIB, CompressionType.ZLIB),  # all ZLIB
    (CompressionType.BROTLI, CompressionType.BROTLI, CompressionType.BROTLI),  # all BROTLI
    (CompressionType.ZSTD, CompressionType.ZSTD, CompressionType.ZSTD),  # all ZSTD
    (CompressionType.ZLIB, CompressionType.BROTLI, CompressionType.ZSTD),  # mixed
])
def test_encoder_decoder_roundtrip(comp_types):
    if not SAMPLE_IMAGE.exists():
        pytest.skip('Sample image not found; run tests/generate_test_assets.py first')

    meta_comp, hotspot_comp, layer_comp = comp_types

    enc = K2SHBWIEncoder()
    enc.set_image(str(SAMPLE_IMAGE))
    test_meta = {
        'title': 'Roundtrip Test',
        'author': 'Tester',
        'description': 'Roundtrip'
    }
    enc.add_metadata(test_meta)
    
    # Set compression types for all sections
    enc.metadata.compression_type = meta_comp
    enc.hotspots_compression = hotspot_comp
    enc.data_layers_compression = layer_comp

    enc.add_hotspot((10,10,100,100), {'note':'h1'})
    enc.add_data_layer('layer1', {'k':'v'})

    out_file = Path(tempfile.gettempdir()) / f'test_roundtrip_{meta_comp.name}.k2sh'
    if out_file.exists():
        out_file.unlink()
    enc.encode(str(out_file))

    dec = K2SHBWIDecoder()
    dec.decode(str(out_file))

    md = dec.get_metadata()
    assert md.get('title') == 'Roundtrip Test'
    assert len(dec.get_hotspots()) >= 1
    assert dec.get_data_layer('layer1')['k'] == 'v'

    # cleanup
    try:
        out_file.unlink()
    except Exception:
        pass
