"""Perceptual image optimization stub

Provides a tiny API that can be expanded to perform psychovisual
optimizations. For now it returns the input bytes unchanged.
"""
from typing import Tuple


def perceptual_optimize(image_bytes: bytes, quality_hint: int = 75) -> Tuple[bytes, dict]:
    """Placeholder that would apply perceptual optimizations.

    Returns (optimized_bytes, metadata).
    """
    # No-op in stub
    return image_bytes, {'quality_hint': quality_hint, 'method': 'noop'}
