"""Context-aware caching (SmartCache) stub

Simple LRU-like cache implementation with optional prediction weight.
This is intentionally lightweight and dependency-free.
"""
from collections import OrderedDict
from typing import Any, Optional


class SmartCache:
    def __init__(self, max_size: int = 128):
        self.max_size = max_size
        self._store = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            value = self._store.pop(key)
            self._store[key] = value
            return value
        return None

    def set(self, key: str, value: Any) -> None:
        if key in self._store:
            self._store.pop(key)
        self._store[key] = value
        if len(self._store) > self.max_size:
            self._store.popitem(last=False)

    def clear(self):
        self._store.clear()
