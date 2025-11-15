"""Core package."""
# Avoid importing submodules at package import time to prevent circular
# import issues when submodules import other parts of this package.
from .errors import CompressionError, ValidationError, FormatError

__all__ = [
    'CompressionError',
    'ValidationError',
    'FormatError'
]