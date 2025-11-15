"""Temprorary file to hold format definitions."""
"""Format definitions for K2SHBWI."""

import enum
from typing import Callable
import zlib

from .errors import CompressionError

class CompressionType(enum.IntEnum):
    """Available compression types."""
    NONE = 0
    ZLIB = 1
    BROTLI = 2
    LZMA = 3
    ZSTD = 4

    @classmethod
    def get_compressor(cls, comp_type: 'CompressionType') -> Callable[[bytes], bytes]:
        """Get the compression function for the given type."""
        # Type validation
        if not isinstance(comp_type, cls):
            raise ValueError(f"Unsupported compression type: {comp_type}")

        # Handle compression types
        if comp_type == cls.NONE:
            return lambda x: x
        elif comp_type == cls.ZLIB:
            return zlib.compress
        elif comp_type == cls.BROTLI:
            try:
                import brotli
                return brotli.compress
            except ImportError:
                raise CompressionError(
                    "brotli library is not installed. Install with: pip install brotli")
        elif comp_type == cls.LZMA:
            try:
                import lzma
                return lzma.compress
            except ImportError:
                raise CompressionError(
                    "lzma library is not available in this Python installation")
        elif comp_type == cls.ZSTD:
            try:
                import zstandard as zstd
                def zstd_compress(b: bytes) -> bytes:
                    cctx = zstd.ZstdCompressor()
                    return cctx.compress(b)
                return zstd_compress
            except ImportError:
                raise CompressionError(
                    "zstandard library is not installed. Install with: pip install zstandard")
                
        # Default handler for unknown types
        return lambda x: x

    @classmethod
    def get_decompressor(cls, comp_type: 'CompressionType') -> Callable[[bytes], bytes]:
        """Get the decompression function for the given type."""
        # Type validation
        if not isinstance(comp_type, cls):
            raise ValueError(f"Unsupported compression type: {comp_type}")

        # Handle decompression types
        if comp_type == cls.NONE:
            return lambda x: x
        elif comp_type == cls.ZLIB:
            return zlib.decompress
        elif comp_type == cls.BROTLI:
            try:
                import brotli
                return brotli.decompress
            except ImportError:
                raise CompressionError(
                    "brotli library is not installed. Install with: pip install brotli")
        elif comp_type == cls.LZMA:
            try:
                import lzma
                return lzma.decompress
            except ImportError:
                raise CompressionError(
                    "lzma library is not available in this Python installation")
        elif comp_type == cls.ZSTD:
            try:
                import zstandard as zstd
                def zstd_decompress(b: bytes) -> bytes:
                    dctx = zstd.ZstdDecompressor()
                    return dctx.decompress(b)
                return zstd_decompress
            except ImportError:
                raise CompressionError(
                    "zstandard library is not installed. Install with: pip install zstandard")
                
        # Default handler for unknown types
        return lambda x: x


class ImageFormat(enum.IntEnum):
    """Image formats for pyramid levels."""
    PNG = 0
    WEBP = 2  # Optional, requires Pillow WebP support