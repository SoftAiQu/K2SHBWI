import tempfile
from pathlib import Path
import pytest

from src.core.encoder import K2SHBWIEncoder
from src.core.decoder import K2SHBWIDecoder

SAMPLE_IMAGE = Path(__file__).parent / 'assets' / 'sample.png'


def test_image_pyramid_roundtrip():
    if not SAMPLE_IMAGE.exists():
        pytest.skip('Sample image not found; generate assets first')

    enc = K2SHBWIEncoder()
    enc.set_image(str(SAMPLE_IMAGE))
    enc.image_pyramid_enabled = True
    enc.adaptive_compression = True

    out_file = Path(tempfile.gettempdir()) / 'test_pyramid.k2sh'
    if out_file.exists():
        out_file.unlink()
    enc.encode(str(out_file))

    dec = K2SHBWIDecoder()
    dec.decode(str(out_file))

    # Expect a parsed image_pyramid list with at least 1 level
    assert hasattr(dec, 'image_pyramid')
    assert isinstance(dec.image_pyramid, list)
    assert len(dec.image_pyramid) >= 1
    # Highest-res data should be available via get_image()
    img = dec.get_image()
    assert img is not None

    try:
        out_file.unlink()
    except Exception:
        pass
