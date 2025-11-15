import sys
from pathlib import Path
ROOT = Path('.').resolve()
sys.path.insert(0, str(ROOT))
from src.core.decoder import K2SHBWIDecoder
p = Path('cli_output.k2sh')
d = K2SHBWIDecoder()
d.decode(str(p))
print('Decoded metadata:', d.get_metadata())
print('Hotspots count:', len(d.get_hotspots()))
img = d.get_image()
if img:
    img.save('cli_extracted.png')
    print('Extracted image saved to cli_extracted.png')
else:
    print('No image extracted')
