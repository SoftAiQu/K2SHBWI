"""
Compression helper wrapper for K2SHBWI

This module provides convenience functions to compress/decompress bytes
using the `CompressionType` defined in `format_spec.py`.

It mirrors the behavior implemented on the `CompressionType` enum but
centralizes a small stable API that other modules (or documentation)
can import from `src.core.compression`.
"""
from typing import Callable, Union

from .format_spec import CompressionType, CompressionError


def _resolve(comp: Union[CompressionType, int, str]) -> CompressionType:
    """Resolve a CompressionType from enum, int or name string.

    Raises CompressionError if the provided value is invalid.
    """
    if isinstance(comp, CompressionType):
        return comp
    try:
        if isinstance(comp, int):
            return CompressionType(comp)
        if isinstance(comp, str):
            return CompressionType[comp]
    except Exception as e:
        raise CompressionError(f"Invalid compression type: {comp}") from e

    raise CompressionError(f"Invalid compression type: {comp}")


def get_compressor(comp: Union[CompressionType, int, str]) -> Callable[[bytes], bytes]:
    """Return a compressor callable for the given compression type."""
    ct = _resolve(comp)
    return CompressionType.get_compressor(ct)


def get_decompressor(comp: Union[CompressionType, int, str]) -> Callable[[bytes], bytes]:
    """Return a decompressor callable for the given compression type."""
    ct = _resolve(comp)
    return CompressionType.get_decompressor(ct)


def compress_bytes(comp: Union[CompressionType, int, str], data: bytes) -> bytes:
    """Compress `data` with the specified compression type."""
    compressor = get_compressor(comp)
    try:
        return compressor(data)
    except Exception as e:
        raise CompressionError(f"Compression failed: {e}") from e


def decompress_bytes(comp: Union[CompressionType, int, str], data: bytes) -> bytes:
    """Decompress `data` with the specified compression type."""
    decompressor = get_decompressor(comp)
    try:
        return decompressor(data)
    except Exception as e:
        raise CompressionError(f"Decompression failed: {e}") from e


__all__ = [
    'get_compressor',
    'get_decompressor',
    'compress_bytes',
    'decompress_bytes',
    'CompressionType',
]
