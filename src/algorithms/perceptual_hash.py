"""Perceptual image hashing stub

Implements a very small average-hash (aHash) using PIL if available,
otherwise falls back to a simple checksum. This keeps the module usable
without heavy dependencies.
"""
from typing import Optional
import hashlib


def average_hash(image_bytes: bytes, hash_size: int = 8) -> str:
    """Return a hex string representing a simple hash.

    This implementation tries to use PIL for an actual aHash. If PIL is
    not available, falls back to SHA256 of bytes (not ideal, but safe).
    """
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes)).convert('L').resize((hash_size, hash_size))
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        bits = ''.join('1' if p > avg else '0' for p in pixels)
        hexstr = f"%0{len(bits)//4}x" % int(bits, 2)
        return hexstr
    except Exception:
        return hashlib.sha256(image_bytes).hexdigest()
