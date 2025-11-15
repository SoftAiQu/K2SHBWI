"""Progressive / lazy loading utilities (stub)

Provides a small ProgressiveLoader class with a simple API used by
viewers or builders to request levels on demand.
"""
from typing import Iterable, Any, Optional


class ProgressiveLoader:
    def __init__(self, levels: Iterable[Any]):
        self.levels = list(levels)

    def get_level(self, idx: int) -> Optional[Any]:
        """Return a level by index or None if out of range."""
        if 0 <= idx < len(self.levels):
            return self.levels[idx]
        return None

    def available_levels(self) -> int:
        return len(self.levels)
