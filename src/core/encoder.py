"""
K2SHBWI Encoder
Handles conversion of images and data into K2SHBWI format
"""

import json
import zlib
import struct
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image, features as _pil_features
import io
import math

# Constants from PIL - handle both old and new PIL versions
def _get_pil_constant(name):
    """Helper to get PIL constants across versions"""
    if hasattr(Image, 'Resampling') and hasattr(Image.Resampling, name):
        return getattr(Image.Resampling, name)
    return getattr(Image, name)

LANCZOS = _get_pil_constant('LANCZOS')
BILINEAR = _get_pil_constant('BILINEAR')

from .format import (
    CompressionType,
    ImageFormat
)
from .format_spec import (
    K2SHBWIHeader,
    K2SHBWIMetadata,
    FeatureFlags,
    HEADER_SIZE,
    MIN_IMAGE_SIZE,
    MAX_IMAGE_SIZE,
)
from .errors import ValidationError, CompressionError, FormatError
from ..algorithms.registry import registry, init_registry
from ..algorithms.smart_compression import adaptive_compress

# Initialize algorithm registry
init_registry()

class K2SHBWIEncoder:
    """Encodes images and data into K2SHBWI format"""
    
    def __init__(self):
        self.header = K2SHBWIHeader()
        self.metadata = K2SHBWIMetadata()
        self.image_data = None
        self.hotspots = []
        self.data_layers = {}
        # Default compression types for sections
        self.hotspots_compression = CompressionType.ZLIB
        self.data_layers_compression = CompressionType.ZLIB
        # Adaptive compression flag: when True encoder chooses the best compressor per-section
        self.adaptive_compression = False
        # Image pyramid support (off by default). When enabled, encoder will
        # generate multiple resolution PNG levels and store them in a
        # pyramid container that the decoder can read.
        self.image_pyramid_enabled = False
        # Pyramid levels (pixel size for the longest side). Default order: high->low->thumb
        self.pyramid_levels = [2048, 1024, 512, 256]
        # Per-level formats: 0=PNG,1=JPEG,2=WEBP
        # If None -> automatic per-level selection (entropy-based)
        self.pyramid_level_formats = None
        # Quality used for JPEG/WEBP when chosen (0-100)
        self.pyramid_quality = 80
        # Optional SSIM support for deciding whether lower-res levels can be lossy.
        # When True, encoder will attempt to compute SSIM between adjacent levels
        # and prefer lossy formats for very high-similarity levels.
        # Enable SSIM-based decisions by default for better automatic format selection.
        # This can be disabled by setting `encoder.pyramid_use_ssim = False`.
        self.pyramid_use_ssim = True
        # thresholds
        # Entropy threshold used when deciding lossy formats (bits per symbol)
        self.pyramid_entropy_threshold = 5.0
        # Be conservative: require near-perfect SSIM before preferring lossy formats
        self.pyramid_ssim_threshold = 0.995
        # Minimum entropy required for SSIM-driven lossy choice (avoid forcing lossy on flat images)
        self.pyramid_min_entropy_for_ssim = 1.0
        # Downsample size used for SSIM comparisons (longest side).
        # Downsampling keeps SSIM fast in CI and for large images.
        self.pyramid_ssim_downsample = 256
        
    def set_image(self, image_path: str):
        """Load and validate the base image"""
        img = Image.open(image_path)
        
        # Convert to standardized format
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA')

        # Validate size and optionally upscale small images to MIN_IMAGE_SIZE
        w, h = img.size
        if w < MIN_IMAGE_SIZE or h < MIN_IMAGE_SIZE:
            target_w = max(w, MIN_IMAGE_SIZE)
            target_h = max(h, MIN_IMAGE_SIZE)
            img = img.resize((target_w, target_h), resample=LANCZOS)

        if w > MAX_IMAGE_SIZE or h > MAX_IMAGE_SIZE:
            raise ValidationError(f"Image too large: {w}x{h} exceeds max {MAX_IMAGE_SIZE}")

        # Store in memory as PNG (lossless base)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        self.image_data = img_byte_arr.getvalue()

        # Set flag (we have at least a base image level)
        self.header.set_feature_flag(FeatureFlags.HAS_IMAGE_PYRAMID)

    def _shannon_entropy(self, img: Image.Image) -> float:
        """Compute Shannon entropy for a grayscale version of the image."""
        hist = img.convert('L').histogram()
        total = sum(hist)
        if total == 0:
            return 0.0
        ent = 0.0
        for c in hist:
            if c:
                p = c / total
                ent -= p * math.log2(p)
        return ent

    def _compute_ssim(self, img1: Image.Image, img2: Image.Image) -> Optional[float]:
        """Try to compute SSIM between two PIL Images.

        First tries to use skimage.metrics.structural_similarity if available.
        If not available (or on error), falls back to a small pure-Python
        implementation that works on grayscale pixel arrays.

        Returns float in [-1,1] or None if inputs are incompatible.
        """
        # Ensure same size; if not, resize img2 to img1 size
        try:
            if img1.size != img2.size:
                img2 = img2.resize(img1.size, resample=BILINEAR)
        except Exception:
            return None

        # Prefer skimage if available
        try:
            # Import at function level to make it optional
            import importlib.util
            if importlib.util.find_spec('skimage'):
                from skimage.metrics import structural_similarity as ssim  # type: ignore
                import numpy as _np
                # Convert images to numpy arrays and ensure correct type
                a = _np.asarray(img1.convert('L'), dtype=_np.float64)
                b = _np.asarray(img2.convert('L'), dtype=_np.float64)
                # Get SSIM score and ensure it's a scalar
                score = ssim(a, b, full=False, data_range=255.0)
                return float(_np.array(score).item())
        except Exception:
            pass

        # NumPy fast path (no skimage) - vectorized variance/covariance
        try:
            import numpy as _np
            a = _np.asarray(img1.convert('L'), dtype=_np.float32)
            b = _np.asarray(img2.convert('L'), dtype=_np.float32)
            if a.size == 0 or b.size == 0 or a.size != b.size:
                return None
            mean_a = a.mean()
            mean_b = b.mean()
            var_a = a.var(ddof=1)
            var_b = b.var(ddof=1)
            cov = _np.mean((a - mean_a) * (b - mean_b)) * (a.size / max(1, a.size - 1))
            L = 255.0
            C1 = (0.01 * L) ** 2
            C2 = (0.03 * L) ** 2
            denom1 = (mean_a * mean_a + mean_b * mean_b + C1)
            denom2 = (var_a + var_b + C2)
            if denom1 == 0 or denom2 == 0:
                return 0.0
            ssim_val = ((2 * mean_a * mean_b + C1) * (2 * cov + C2)) / (denom1 * denom2)
            return float(ssim_val)
        except Exception:
            pass

        # Pure-Python fallback (slow): operate on lists. To keep this fast for
        # large images (CI), downsample both images to a small thumbnail first.
        try:
            # downsample to thumbnail with longest side == pyramid_ssim_downsample
            max_side = int(self.pyramid_ssim_downsample)
            if max(img1.size) > max_side:
                img1_small = img1.copy()
                img1_small.thumbnail((max_side, max_side), resample=LANCZOS)
            else:
                img1_small = img1
            if max(img2.size) > max_side:
                img2_small = img2.copy()
                img2_small.thumbnail((max_side, max_side), resample=LANCZOS)
            else:
                img2_small = img2

            # Convert image data to list safely
            a_bytes = [x for x in img1_small.convert('L').getdata()]
            b_bytes = [x for x in img2_small.convert('L').getdata()]
            n = len(a_bytes)
            if n == 0 or n != len(b_bytes):
                return None
            mean_a = sum(a_bytes) / n
            mean_b = sum(b_bytes) / n
            var_a = sum((x - mean_a) ** 2 for x in a_bytes) / (n - 1 if n > 1 else 1)
            var_b = sum((y - mean_b) ** 2 for y in b_bytes) / (n - 1 if n > 1 else 1)
            cov = sum((a_bytes[i] - mean_a) * (b_bytes[i] - mean_b) for i in range(n)) / (n - 1 if n > 1 else 1)
            L = 255.0
            C1 = (0.01 * L) ** 2
            C2 = (0.03 * L) ** 2
            denom1 = (mean_a * mean_a + mean_b * mean_b + C1)
            denom2 = (var_a + var_b + C2)
            if denom1 == 0 or denom2 == 0:
                return 0.0
            ssim_val = ((2 * mean_a * mean_b + C1) * (2 * cov + C2)) / (denom1 * denom2)
            return float(ssim_val)
        except Exception:
            return None


    def _choose_format_for_level(self, img: Image.Image, prev_img: Optional[Image.Image] = None) -> int:
        """Return format id for a level using simple heuristics.

        - If image has an alpha channel -> PNG (0)
        - Else compute entropy; if entropy > threshold -> lossy (WEBP if available else JPEG)
        - Otherwise PNG
        """
        # Preserve alpha
        bands = img.getbands()
        if 'A' in bands:
            return 0
        ent = self._shannon_entropy(img)

        # If SSIM use is enabled and we have a previous level, compute SSIM
        if self.pyramid_use_ssim and prev_img is not None:
            s = self._compute_ssim(img, prev_img)
            if s is not None:
                # Only trust SSIM to prefer lossy when the SSIM is extremely high
                # AND the image entropy is not trivially low (e.g., flat/single-color).
                if s >= self.pyramid_ssim_threshold and ent > self.pyramid_min_entropy_for_ssim:
                    try:
                        webp_ok = _pil_features.check('webp')
                    except Exception:
                        webp_ok = False
                    return 2 if webp_ok else 1

        # fallback to entropy-only decision
        if ent > self.pyramid_entropy_threshold:
            try:
                webp_ok = _pil_features.check('webp')
            except Exception:
                webp_ok = False
            return 2 if webp_ok else 1
        return 0

    def _generate_pyramid_blob(self, img: Image.Image) -> bytes:
        """Generate a pyramid container bytes for the provided PIL Image.

        Container format (binary):
          marker (1B) = 0x7F
          num_levels (1B)
          for each level:
            level_id (1B)
            width (4B little)
            height (4B little)
            format (1B) (0=PNG)
            quality (1B) (reserved)
            comp_type (1B)
            comp_len (4B little)
            comp_payload (comp_len bytes)

        Each level image is encoded as PNG bytes, then compressed using
        the adaptive compressor (if enabled) or the encoder's preferred compressor.
        """
        import io
        from struct import pack

        marker = b'\x7F'
        levels = []

        prev_level_img = None
        for idx, size in enumerate(self.pyramid_levels):
            # Resize preserving aspect ratio to have longest side == size
            w, h = img.size
            if max(w, h) <= size:
                level_img = img.copy()
            else:
                if w >= h:
                    nw = size
                    nh = int(h * (size / w))
                else:
                    nh = size
                    nw = int(w * (size / h))
                level_img = img.resize((nw, nh), resample=LANCZOS)

            buf = io.BytesIO()

            # Decide format for this level. If pyramid_level_formats is None -> auto-select by entropy.
            if self.pyramid_level_formats is None:
                fmt = self._choose_format_for_level(level_img, prev_level_img)
            else:
                fmt = self.pyramid_level_formats[idx] if idx < len(self.pyramid_level_formats) else 0

            # 0=PNG, 1=JPEG, 2=WEBP
            if fmt == 0:
                level_img.save(buf, format='PNG')
            elif fmt == 1:
                # JPEG doesn't support alpha; convert if necessary
                save_img = level_img.convert('RGB')
                save_img.save(buf, format='JPEG', quality=self.pyramid_quality)
            elif fmt == 2:
                try:
                    level_img.save(buf, format='WEBP', quality=self.pyramid_quality)
                except Exception:
                    # Fallback to JPEG (if alpha then PNG)
                    try:
                        save_img = level_img.convert('RGB')
                        save_img.save(buf, format='JPEG', quality=self.pyramid_quality)
                        fmt = 1
                    except Exception:
                        level_img.save(buf, format='PNG')
                        fmt = 0
            else:
                level_img.save(buf, format='PNG')

            png_bytes = buf.getvalue()

            # Choose compressor
            if self.adaptive_compression:
                comp_bytes, comp_type = adaptive_compress(png_bytes, data_type='image')
            else:
                compressor = CompressionType.get_compressor(self.data_layers_compression)
                comp_bytes = compressor(png_bytes)
                comp_type = self.data_layers_compression

            levels.append((idx, level_img.width, level_img.height, fmt, self.pyramid_quality, comp_type.value, comp_bytes))
            # remember this level for next iteration SSIM comparison
            prev_level_img = level_img.copy()

        parts = [marker, pack('<B', len(levels))]
        for lvl in levels:
            idx, w, h, fmt, quality, comp_type_val, comp_bytes = lvl
            parts.append(pack('<BII', idx, w, h))
            parts.append(pack('<BB', fmt, quality))
            parts.append(pack('<BI', comp_type_val, len(comp_bytes)))
            parts.append(comp_bytes)

        return b''.join(parts)
        
    def add_metadata(self, metadata: Dict[str, Any]):
        """Add metadata to the file"""
        self.metadata.data = metadata
        self.metadata.compression_type = CompressionType.ZLIB
        self.header.set_feature_flag(FeatureFlags.HAS_METADATA)
        
    def add_hotspot(self, coords: tuple, data: Dict[str, Any]):
        """Add a hotspot with associated data"""
        self.hotspots.append({
            'coords': coords,
            'data': data
        })
        self.header.set_feature_flag(FeatureFlags.HAS_HOTSPOTS)
        
    def add_data_layer(self, layer_id: str, data: Dict[str, Any]):
        """Add a data layer"""
        self.data_layers[layer_id] = data
        self.header.set_feature_flag(FeatureFlags.HAS_DATA_LAYERS)
        
    def encode(self, output_path: str):
        """Encode everything into K2SHBWI format"""
        with open(output_path, 'wb') as f:
            # Write header placeholder (don't validate yet) - reserve HEADER_SIZE bytes
            f.write(b'\x00' * HEADER_SIZE)
            current_offset = HEADER_SIZE
            
            # Write metadata
            if self.header.flags & FeatureFlags.HAS_METADATA.value:
                self.header.metadata_offset = current_offset
                try:
                    if self.adaptive_compression:
                        raw = json.dumps(self.metadata.data, separators=(',', ':')).encode('utf-8')
                        compressed, chosen = adaptive_compress(raw, data_type='json')
                        f.write(struct.pack('<IB', len(compressed), chosen.value))
                        f.write(compressed)
                    else:
                        packed_meta, total_len = self.metadata.pack()
                        f.write(packed_meta)
                except Exception as e:
                    raise CompressionError(f"Failed to pack metadata: {e}")

                current_offset = f.tell()
            
            # Write image data (single blob or pyramid container)
            if self.image_data:
                self.header.image_pyramid_offset = current_offset
                if self.image_pyramid_enabled:
                    # Build pyramid container from the in-memory image
                    import io as _io
                    from PIL import Image as _Image
                    img = _Image.open(_io.BytesIO(self.image_data))
                    pyramid_blob = self._generate_pyramid_blob(img)
                    f.write(struct.pack('<I', len(pyramid_blob)))
                    f.write(pyramid_blob)
                else:
                    # Write image blob (length + bytes)
                    f.write(struct.pack('<I', len(self.image_data)))
                    f.write(self.image_data)
                current_offset = f.tell()
            
            # Write hotspots
            if self.hotspots:
                self.header.hotspot_map_offset = current_offset
                hotspots_json = json.dumps(self.hotspots).encode('utf-8')
                if self.adaptive_compression:
                    compressed, chosen = adaptive_compress(hotspots_json, data_type='json')
                    f.write(struct.pack('<IB', len(compressed), chosen.value))
                    f.write(compressed)
                else:
                    compressor = CompressionType.get_compressor(self.hotspots_compression)
                    compressed = compressor(hotspots_json)
                    f.write(struct.pack('<IB', len(compressed), self.hotspots_compression.value))
                    f.write(compressed)
                current_offset = f.tell()
            
            # Write data layers
            if self.data_layers:
                self.header.data_layers_offset = current_offset
                layers_json = json.dumps(self.data_layers).encode('utf-8')
                if self.adaptive_compression:
                    compressed, chosen = adaptive_compress(layers_json, data_type='json')
                    f.write(struct.pack('<IB', len(compressed), chosen.value))
                    f.write(compressed)
                else:
                    compressor = CompressionType.get_compressor(self.data_layers_compression)
                    compressed = compressor(layers_json)
                    f.write(struct.pack('<IB', len(compressed), self.data_layers_compression.value))
                    f.write(compressed)
                current_offset = f.tell()
            
            # Go back and update header with final offsets
            f.seek(0)
            f.write(self.header.pack())