"""
K2SHBWI Format Specification Implementation
Defines the binary format structure and constants for the K2SHBWI file format.

File Structure:
    - Header (56 bytes)
        - Magic bytes (4 bytes)
        - Version (4 bytes)
        - Feature flags (2 bytes)
        - Section offsets (32 bytes)
        - Reserved (16 bytes)
    - Metadata Section
        - Length (4 bytes)
        - Compression type (1 byte)
        - Compressed JSON data
    - Image Pyramid
        - Number of levels (1 byte)
        - Level data
    - Hotspot Map
        - Length (4 bytes)
        - Compression type (1 byte)
        - Compressed JSON data
    - Data Layers
        - Length (4 bytes)
        - Compression type (1 byte)
        - Compressed JSON data
"""

from enum import Enum, auto
from .format import CompressionType
from typing import Dict, Any, List, Optional, Tuple
import struct
import json
import zlib

# Magic bytes and version constants
MAGIC_BYTES = b'K2SH'
CURRENT_VERSION_MAJOR = 1
CURRENT_VERSION_MINOR = 0

# File format constants
HEADER_SIZE = 56
MIN_IMAGE_SIZE = 512  # Minimum image dimension
MAX_IMAGE_SIZE = 16384  # Maximum image dimension
MAX_METADATA_SIZE = 1024 * 1024  # 1MB
MAX_HOTSPOTS = 1000  # Maximum number of hotspots per image

class K2SHBWIError(Exception):
    """Base exception for all K2SHBWI-related errors"""
    pass

class ValidationError(K2SHBWIError):
    """Raised when file validation fails"""
    pass

class CompressionError(K2SHBWIError):
    """Raised when compression/decompression fails"""
    pass

class FormatError(K2SHBWIError):
    """Raised when file format is invalid"""
    pass

# CompressionType is defined centrally in src/core/format.py. Import it
# here to avoid duplicate definitions and potential inconsistencies.

class FeatureFlags(Enum):
    """Feature flags for K2SHBWI files"""
    NONE = 0
    HAS_METADATA = 1 << 0
    HAS_IMAGE_PYRAMID = 1 << 1
    HAS_HOTSPOTS = 1 << 2
    HAS_DATA_LAYERS = 1 << 3
    HAS_ENCRYPTION = 1 << 4  # Reserved for future encryption support
    IS_COMPRESSED = 1 << 5   # Indicates if any section is compressed
    HAS_AUDIO = 1 << 6      # Reserved for future audio support
    HAS_VIDEO = 1 << 7      # Reserved for future video support
    
    @classmethod
    def validate_flags(cls, flags: int) -> bool:
        """Validate feature flags"""
        # Check if any undefined flags are set
        valid_flags = sum(flag.value for flag in cls)
        return (flags & ~valid_flags) == 0

class K2SHBWIHeader:
    """
    Represents the binary header of a K2SHBWI file.
    
    The header contains:
    - Magic bytes (K2SH)
    - Version information
    - Feature flags
    - Section offsets
    - Reserved space for future use
    """
    
    def __init__(self):
        self.version_major: int = CURRENT_VERSION_MAJOR
        self.version_minor: int = CURRENT_VERSION_MINOR
        self.flags: int = 0
        self.metadata_offset: int = 0
        self.image_pyramid_offset: int = 0
        self.hotspot_map_offset: int = 0
        self.data_layers_offset: int = 0
        
    def validate(self) -> bool:
        """
        Validate header contents
        
        Returns:
            bool: True if header is valid
            
        Raises:
            ValidationError: If header validation fails
        """
        # Version check
        if self.version_major > CURRENT_VERSION_MAJOR:
            raise ValidationError(f"Unsupported version: {self.version_major}.{self.version_minor}")
            
        # Flag validation
        if not FeatureFlags.validate_flags(self.flags):
            raise ValidationError("Invalid feature flags")
            
        # Offset validation
        if self.flags & FeatureFlags.HAS_METADATA.value:
            if self.metadata_offset < HEADER_SIZE:
                raise ValidationError("Invalid metadata offset")
                
        if self.flags & FeatureFlags.HAS_IMAGE_PYRAMID.value:
            if self.image_pyramid_offset < HEADER_SIZE:
                raise ValidationError("Invalid image pyramid offset")
                
        if self.flags & FeatureFlags.HAS_HOTSPOTS.value:
            if self.hotspot_map_offset < HEADER_SIZE:
                raise ValidationError("Invalid hotspot map offset")
                
        if self.flags & FeatureFlags.HAS_DATA_LAYERS.value:
            if self.data_layers_offset < HEADER_SIZE:
                raise ValidationError("Invalid data layers offset")
                
        return True
    
    def pack(self) -> bytes:
        """
        Pack header into bytes
        
        Returns:
            bytes: Packed header data
            
        Raises:
            ValidationError: If header validation fails
        """
        self.validate()
        
        try:
            # Header layout (total 56 bytes):
            # 4s  -> magic (4)
            # H   -> version_major (2)
            # H   -> version_minor (2)
            # H   -> flags (2)
            # Q*4 -> offsets (32)
            # 14s -> reserved (14)  => total 56
            return struct.pack(
                '<4sHHHQQQQ14s',
                MAGIC_BYTES,
                self.version_major,
                self.version_minor,
                self.flags,
                self.metadata_offset,
                self.image_pyramid_offset,
                self.hotspot_map_offset,
                self.data_layers_offset,
                b'\x00' * 14  # Reserved bytes (14 to keep header 56 bytes)
            )
        except struct.error as e:
            raise FormatError(f"Failed to pack header: {e}")
    
    @classmethod
    def unpack(cls, data: bytes) -> 'K2SHBWIHeader':
        """
        Unpack header from bytes
        
        Args:
            data: Raw header bytes
            
        Returns:
            K2SHBWIHeader: Unpacked header object
            
        Raises:
            ValidationError: If header data is invalid
            FormatError: If unpacking fails
        """
        if len(data) < HEADER_SIZE:
            raise ValidationError(f"Header too small: {len(data)} bytes")
            
        try:
            magic, major, minor, flags_val, meta_off, img_off, hot_off, data_off, _ = struct.unpack(
                '<4sHHHQQQQ14s', data[:HEADER_SIZE]
            )
        except struct.error as e:
            raise FormatError(f"Failed to unpack header: {e}")
            
        if magic != MAGIC_BYTES:
            raise ValidationError(f"Invalid magic bytes: {magic}")
            
        header = cls()
        header.version_major = major
        header.version_minor = minor
        header.flags = flags_val
        header.metadata_offset = meta_off
        header.image_pyramid_offset = img_off
        header.hotspot_map_offset = hot_off
        header.data_layers_offset = data_off
        
        # Validate the unpacked header
        header.validate()
        
        return header
        
    def get_section_offsets(self) -> Dict[str, int]:
        """
        Get a dictionary of all section offsets
        
        Returns:
            Dict[str, int]: Section name to offset mapping
        """
        return {
            'metadata': self.metadata_offset,
            'image_pyramid': self.image_pyramid_offset,
            'hotspot_map': self.hotspot_map_offset,
            'data_layers': self.data_layers_offset
        }
        
    def set_feature_flag(self, flag: FeatureFlags):
        """
        Set a feature flag
        
        Args:
            flag: Feature flag to set
        """
        self.flags |= flag.value
        
    def clear_feature_flag(self, flag: FeatureFlags):
        """
        Clear a feature flag
        
        Args:
            flag: Feature flag to clear
        """
        self.flags &= ~flag.value
        
    def has_feature(self, flag: FeatureFlags) -> bool:
        """
        Check if a feature flag is set
        
        Args:
            flag: Feature flag to check
            
        Returns:
            bool: True if flag is set
        """
        return bool(self.flags & flag.value)

class K2SHBWIMetadata:
    """Represents the metadata section of a K2SHBWI file.

    The metadata section contains:
    - Length (4 bytes)
    - Compression type (1 byte)
    - Compressed JSON data containing:
        - title: str
        - author: str
        - created_date: str (ISO format with UTC timezone)
        - modified_date: str (ISO format with UTC timezone)
        - description: str
        - tags: List[str]
        - custom_fields: Dict[str, Any]
    """

    # Require title and author; created_date will be auto-filled if missing
    REQUIRED_FIELDS = {'title', 'author'}

    def __init__(self):
        self.compression_type: CompressionType = CompressionType.ZLIB
        self.data: Dict[str, Any] = {
            'title': '',
            'author': '',
            'created_date': '',
            'modified_date': '',
            'description': '',
            'tags': [],
            'custom_fields': {}
        }

    def validate(self) -> bool:
        """Validate metadata contents.

        Raises:
            ValidationError: if required fields are missing or types are invalid.
        """
        # Required fields
        for field in self.REQUIRED_FIELDS:
            if not self.data.get(field):
                raise ValidationError(f"Missing required metadata field: {field}")

        # Auto-fill created_date if missing
        if not self.data.get('created_date'):
            from datetime import datetime, UTC
            self.data['created_date'] = datetime.now(UTC).isoformat()

        # Types
        if not isinstance(self.data.get('tags', []), list):
            raise ValidationError('Tags must be a list')

        if not isinstance(self.data.get('custom_fields', {}), dict):
            raise ValidationError('Custom fields must be a dictionary')

        # Dates (if present) must be ISO-formatted with UTC timezone
        from datetime import datetime
        from zoneinfo import ZoneInfo
        try:
            if self.data.get('created_date'):
                dt = datetime.fromisoformat(self.data['created_date'])
                if dt.tzinfo is None:
                    raise ValidationError('created_date must have timezone information')
            if self.data.get('modified_date'):
                dt = datetime.fromisoformat(self.data['modified_date'])
                if dt.tzinfo is None:
                    raise ValidationError('modified_date must have timezone information')
        except Exception as e:
            raise ValidationError(f'Invalid date format: {e}')

        return True

    def pack(self) -> Tuple[bytes, int]:
        """Pack metadata into bytes and return (packed_bytes, total_length).

        Uses the configured compression_type. Raises CompressionError on failures.
        """
        self.validate()

        try:
            raw = json.dumps(self.data, separators=(',', ':')).encode('utf-8')
            compressor = CompressionType.get_compressor(self.compression_type)
            compressed = compressor(raw)
            header = struct.pack('<IB', len(compressed), self.compression_type.value)
            return header + compressed, len(header) + len(compressed)
        except Exception as e:
            raise CompressionError(f'Failed to pack metadata: {e}')

    @classmethod
    def unpack(cls, data: bytes) -> 'K2SHBWIMetadata':
        """Unpack metadata from raw bytes and return a K2SHBWIMetadata instance.

        Expects first 5 bytes to be: <I (length)><B (compression type)> followed by compressed payload.
        """
        try:
            length, comp_val = struct.unpack('<IB', data[:5])
            payload = data[5:5+length]
            comp_type = CompressionType(comp_val)
            decompressor = CompressionType.get_decompressor(comp_type)
            raw = decompressor(payload)
            inst = cls()
            inst.compression_type = comp_type
            inst.data = json.loads(raw)
            inst.validate()
            return inst
        except Exception as e:
            raise FormatError(f'Failed to unpack metadata: {e}')

    def update(self, **kwargs) -> None:
        """Update metadata fields in-place."""
        self.data.update(kwargs)