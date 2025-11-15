from PIL import Image
from src.core.encoder import K2SHBWIEncoder
from src.core.decoder import K2SHBWIDecoder
import io

# create solid color image in memory
img = Image.new('RGB', (512,512), color=(50,50,50))
buf = io.BytesIO()
img.save(buf, format='PNG')
img_bytes = buf.getvalue()

p = 'tmp_solid.png'
with open(p, 'wb') as f:
    f.write(img_bytes)

enc = K2SHBWIEncoder()
enc.set_image(p)
enc.image_pyramid_enabled = True
enc.pyramid_level_formats = None
# print current thresholds
print('entropy_threshold', enc.pyramid_entropy_threshold)
print('ssim_threshold', enc.pyramid_ssim_threshold)
print('min_entropy_for_ssim', getattr(enc, 'pyramid_min_entropy_for_ssim', None))

out = 'tmp_out.k2sh'
enc.encode(out)

dec = K2SHBWIDecoder()
dec.decode(out)
print('formats:', [l['format'] for l in dec.image_pyramid])
