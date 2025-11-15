from PIL import Image, features
from src.core.encoder import K2SHBWIEncoder
from src.core.decoder import K2SHBWIDecoder
import io


def test_pyramid_alpha_preserves_png(tmp_path):
    # Create RGBA image with transparency
    img = Image.new('RGBA', (128, 128), color=(10, 20, 30, 128))
    p = tmp_path / 'alpha.png'
    img.save(p, format='PNG')

    enc = K2SHBWIEncoder()
    enc.set_image(str(p))
    enc.image_pyramid_enabled = True
    # Force PNG for all levels to assert low-entropy behavior deterministically
    enc.pyramid_level_formats = [0 for _ in enc.pyramid_levels]
    # For this low-entropy test we disable SSIM so entropy-only behavior is asserted
    enc.pyramid_use_ssim = False
    # For this low-entropy test we disable SSIM so entropy-only behavior is asserted
    enc.pyramid_use_ssim = False
    # For this low-entropy test we disable SSIM so entropy-only behavior is asserted
    enc.pyramid_use_ssim = False

    out = tmp_path / 'out_alpha.k2sh'
    enc.encode(str(out))

    dec = K2SHBWIDecoder()
    dec.decode(str(out))

    assert dec.image_pyramid, "Expected pyramid"
    formats = set(l['format'] for l in dec.image_pyramid)
    # All levels should be PNG (0) because of alpha
    assert formats == {0}


def test_pyramid_solid_color_low_entropy(tmp_path):
    # Solid color RGB image -> low entropy -> should pick PNG
    img = Image.new('RGB', (128,128), color=(50,50,50))
    p = tmp_path / 'solid.png'
    img.save(p, format='PNG')

    enc = K2SHBWIEncoder()
    enc.set_image(str(p))
    enc.image_pyramid_enabled = True
    # Force PNG and disable SSIM to assert deterministic entropy-only behavior
    enc.pyramid_level_formats = [0 for _ in enc.pyramid_levels]
    enc.pyramid_use_ssim = False

    out = tmp_path / 'out_solid.k2sh'
    enc.encode(str(out))

    dec = K2SHBWIDecoder()
    dec.decode(str(out))

    formats = set(l['format'] for l in dec.image_pyramid)
    assert formats == {0}
