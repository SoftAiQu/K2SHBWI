"""
K2SHBWI Decoder
Handles extraction of images and data from K2SHBWI format
"""

import json
import zlib
import struct
from typing import Dict, Any, Tuple, Optional
from PIL import Image
import io

from .format_spec import (
    K2SHBWIHeader,
    K2SHBWIMetadata,
    CompressionType,
    FeatureFlags
)
from .format_spec import FormatError

class K2SHBWIDecoder:
    """Decodes K2SHBWI format back into images and data"""
    
    def __init__(self):
        self.header = None
        self.metadata = None
        self.image_data = None
        self.image_pyramid = []
        self.hotspots = []
        self.data_layers = {}
        
    def decode(self, file_path: str):
        """Decode a K2SHBWI file"""
        with open(file_path, 'rb') as f:
            # Read and validate header
            header_data = f.read(56)
            self.header = K2SHBWIHeader.unpack(header_data)
            
            # Read metadata if present
            if self.header.flags & FeatureFlags.HAS_METADATA.value:
                # Read packed metadata (length + comp_type + payload) and use helper to unpack
                f.seek(self.header.metadata_offset)
                # Read length (4) + comp type (1)
                header5 = f.read(5)
                if len(header5) < 5:
                    raise FormatError("Truncated metadata header")
                length, = struct.unpack('<I', header5[:4])
                # read remaining payload
                payload = f.read(length)
                meta_blob = header5 + payload
                # Use K2SHBWIMetadata.unpack to handle different compression types
                meta_obj = K2SHBWIMetadata.unpack(meta_blob)
                self.metadata = meta_obj.data
            
            # Read image data if present
            if self.header.flags & FeatureFlags.HAS_IMAGE_PYRAMID.value:
                f.seek(self.header.image_pyramid_offset)
                size = struct.unpack('<I', f.read(4))[0]
                payload = f.read(size)

                # Detect pyramid container marker (0x7F). If present, parse levels;
                # otherwise treat payload as a single-image blob (PNG/JPEG bytes).
                if payload and payload[0] == 0x7F:
                    # parse pyramid container
                    try:
                        from struct import unpack
                        off = 1
                        num_levels = payload[off]
                        off += 1
                        levels = []
                        for _ in range(num_levels):
                            level_id = payload[off]
                            off += 1
                            w = unpack('<I', payload[off:off+4])[0]; off += 4
                            h = unpack('<I', payload[off:off+4])[0]; off += 4
                            fmt = payload[off]; off += 1
                            quality = payload[off]; off += 1
                            comp_type_val = unpack('<B', payload[off:off+1])[0]; off += 1
                            comp_len = unpack('<I', payload[off:off+4])[0]; off += 4
                            comp_payload = payload[off:off+comp_len]; off += comp_len
                            try:
                                comp_type = CompressionType(comp_type_val)
                                decompressor = CompressionType.get_decompressor(comp_type)
                                img_bytes = decompressor(comp_payload)
                            except Exception as e:
                                raise FormatError(f"Failed to decompress pyramid level: {e}")
                            levels.append({'level_id': level_id, 'width': w, 'height': h, 'format': fmt, 'quality': quality, 'data': img_bytes})
                        # store pyramid
                        self.image_pyramid = levels
                        # set image_data to highest resolution available
                        if levels:
                            self.image_data = levels[0]['data']
                        else:
                            self.image_data = None
                    except Exception as e:
                        raise FormatError(f"Failed to parse image pyramid: {e}")
                else:
                    # legacy single image blob
                    self.image_data = payload
            
            # Read hotspots if present
            if self.header.flags & FeatureFlags.HAS_HOTSPOTS.value:
                f.seek(self.header.hotspot_map_offset)
                # Read length and compression type
                length, comp_val = struct.unpack('<IB', f.read(5))
                compressed = f.read(length)
                try:
                    comp_type = CompressionType(comp_val)
                    decompressor = CompressionType.get_decompressor(comp_type)
                    raw = decompressor(compressed)
                except Exception as e:
                    raise FormatError(f"Failed to decompress hotspots: {e}")
                self.hotspots = json.loads(raw)
            
            # Read data layers if present
            if self.header.flags & FeatureFlags.HAS_DATA_LAYERS.value:
                f.seek(self.header.data_layers_offset)
                # Read length and compression type
                length, comp_val = struct.unpack('<IB', f.read(5))
                compressed = f.read(length)
                try:
                    comp_type = CompressionType(comp_val)
                    decompressor = CompressionType.get_decompressor(comp_type)
                    raw = decompressor(compressed)
                except Exception as e:
                    raise FormatError(f"Failed to decompress data layers: {e}")
                self.data_layers = json.loads(raw)
    
    def get_image(self) -> Optional[Image.Image]:
        """Extract the base image"""
        if self.image_data:
            return Image.open(io.BytesIO(self.image_data))
        return None
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get the metadata"""
        return self.metadata or {}
    
    def get_hotspots(self) -> list:
        """Get the hotspot data"""
        return self.hotspots
    
    def get_data_layer(self, layer_id: str) -> Dict[str, Any]:
        """Get a specific data layer"""
        return self.data_layers.get(layer_id, {})