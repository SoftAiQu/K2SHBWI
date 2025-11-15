import io
import random
from PIL import Image, features
from src.core.encoder import K2SHBWIEncoder
from src.core.decoder import K2SHBWIDecoder
import pytest


def _make_noise_image(size=(128, 128)):
    # create RGB noise image
    img = Image.new('RGB', size)
    pixels = [ (random.randint(0,255), random.randint(0,255), random.randint(0,255)) for _ in range(size[0]*size[1]) ]
    img.putdata(pixels)
    return img


def _save_temp_image(tmp_path, img: Image.Image):
    p = tmp_path / 'img.png'
    img.save(p, format='PNG')
    return str(p)


def test_pyramid_auto_formats(tmp_path):
    # Create an encoder with auto-selection and a noise image to encourage lossy selection
    img = _make_noise_image((128,128))
    img_path = _save_temp_image(tmp_path, img)

    enc = K2SHBWIEncoder()
    enc.set_image(img_path)
    enc.image_pyramid_enabled = True
    enc.pyramid_level_formats = None
    enc.pyramid_quality = 75

    out = tmp_path / 'out.k2sh'
    enc.encode(str(out))

    dec = K2SHBWIDecoder()
    dec.decode(str(out))

    # Should have a pyramid with one or more levels
    assert dec.image_pyramid, "Image pyramid expected"
    formats = set(l['format'] for l in dec.image_pyramid)
    assert formats.issubset({0,1,2})

    # If runtime lacks webp support, ensure no level is flagged as webp
    webp_ok = False
    try:
        webp_ok = bool(features.check('webp'))
    except Exception:
        webp_ok = False
    if not webp_ok:
        assert 2 not in formats


def test_ssim_helper_presence():
    # If skimage is available, ensure _compute_ssim returns ~1.0 for identical images
    enc = K2SHBWIEncoder()
    try:
        from skimage.metrics import structural_similarity as ssim
    except Exception:
        pytest.skip('skimage not installed; skipping SSIM behavior test')

    img1 = Image.new('RGB', (64,64), color=(123, 222, 100))
    img2 = img1.copy()
    score = enc._compute_ssim(img1, img2)
    assert score is not None
    assert score > 0.999
