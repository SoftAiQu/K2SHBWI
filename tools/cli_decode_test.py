import sys
from pathlib import Path
import pytest
from src.core.decoder import K2SHBWIDecoder

# Setup path
ROOT = Path('.').resolve()
sys.path.insert(0, str(ROOT))

# Check if file exists
p = Path('cli_output.k2sh')
if not p.exists():
    pytest.skip("Skipping CLI decode test: cli_output.k2sh not present", allow_module_level=True)

# Decode the file
d = K2SHBWIDecoder()
d.decode(str(p))

print('Decoded metadata:', d.get_metadata())
print('Hotspots count:', len(d.get_hotspots()))

# Extract and save image
img = d.get_image()
if img:
    img.save('cli_extracted.png')
    print('Extracted image saved to cli_extracted.png')
else:
    print('No image extracted')
