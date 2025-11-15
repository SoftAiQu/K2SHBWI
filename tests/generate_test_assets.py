from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
from datetime import datetime, UTC

out_dir = Path(__file__).parent / "assets"
out_dir.mkdir(exist_ok=True)

# Create PNG
img = Image.new('RGBA', (512,512), (255,255,255,255))
d = ImageDraw.Draw(img)
d.rectangle([50,50,200,200], outline=(255,0,0,255), width=4)
d.text((60,60), "Sample PNG", fill=(0,0,0,255))
img.save(out_dir / 'sample.png')

# Create JPG
img_jpg = Image.new('RGB', (512,512), (240,240,240))
dj = ImageDraw.Draw(img_jpg)
dj.ellipse([300,100,450,250], outline=(0,128,0), width=4)
dj.text((310,110), "Sample JPG", fill=(0,0,0))
img_jpg.save(out_dir / 'sample.jpg', quality=85)

# Create metadata.json
metadata = {
    "title": "Sample K2SHBWI Asset",
    "author": "Test",
    "created_date": datetime.now(UTC).isoformat(),
    "modified_date": datetime.now(UTC).isoformat(),
    "description": "Auto-generated test metadata",
    "tags": ["test", "sample"],
    "custom_fields": {"example": 123}
}
with open(out_dir / 'metadata.json', 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2)

# Create hotspots.json
hotspots = [
    {"id": 1, "coords": [50,50,200,200], "layer": "layer1"},
    {"id": 2, "coords": [300,100,450,250], "layer": "layer2"}
]
with open(out_dir / 'hotspots.json', 'w', encoding='utf-8') as f:
    json.dump(hotspots, f, indent=2)

print(f"Generated test assets in: {out_dir}")
