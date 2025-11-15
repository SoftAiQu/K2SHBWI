"""Multi-level compression strategy stub

Provides a thin wrapper that can combine compressors by preference.
This stub picks zlib for everything to keep dependencies minimal.
"""
from typing import List, Tuple
import zlib


class MultiLevelCompressor:
    def __init__(self, strategies: List[str] = None):
        self.strategies = strategies or ['zlib']

    def compress(self, data: bytes) -> Tuple[bytes, str]:
        # Always use zlib in this stub
        return zlib.compress(data), 'zlib'

    def decompress(self, data: bytes, algorithm: str) -> bytes:
        if algorithm == 'zlib':
            return zlib.decompress(data)
        raise NotImplementedError()
