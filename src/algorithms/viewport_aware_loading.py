"""Viewport-aware progressive loading stub

Simple helper that filters hotspots by viewport rectangle.
"""
from typing import List, Dict, Any, Tuple


def get_visible_hotspots(hotspots: List[Dict[str, Any]], viewport: Tuple[int,int,int,int]) -> List[Dict[str, Any]]:
    """Return hotspots whose bounding box intersects the viewport.

    Hotspot format expected: {'coords': [x1,y1,x2,y2], ...}
    """
    x1v, y1v, x2v, y2v = viewport
    visible = []
    for h in hotspots:
        x1, y1, x2, y2 = h.get('coords', (0,0,0,0))
        if x2 < x1v or x1 > x2v or y2 < y1v or y1 > y2v:
            continue
        visible.append(h)
    return visible
