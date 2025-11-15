import json
import tempfile
from pathlib import Path

import pytest

from src.core.encoder import K2SHBWIEncoder
from src.core.decoder import K2SHBWIDecoder


SAMPLE_IMAGE = Path(__file__).parent / 'assets' / 'sample.png'


def test_encoder_decoder_adaptive_roundtrip():
    # Requires sample image
    if not SAMPLE_IMAGE.exists():
        pytest.skip('Sample image not found; generate assets first')

    enc = K2SHBWIEncoder()
    enc.set_image(str(SAMPLE_IMAGE))
    enc.add_metadata({'title': 'Adaptive Test', 'author': 'Tester'})
    enc.add_hotspot((10, 10, 50, 50), {'note': 'h1'})
    enc.add_data_layer('layer1', {'k': 'v'})
    enc.adaptive_compression = True

    out_file = Path(tempfile.gettempdir()) / 'test_adaptive.k2sh'
    if out_file.exists():
        out_file.unlink()
    enc.encode(str(out_file))

    dec = K2SHBWIDecoder()
    dec.decode(str(out_file))

    md = dec.get_metadata()
    assert md.get('title') == 'Adaptive Test'
    assert len(dec.get_hotspots()) >= 1
    assert dec.get_data_layer('layer1')['k'] == 'v'

    try:
        out_file.unlink()
    except Exception:
        pass
