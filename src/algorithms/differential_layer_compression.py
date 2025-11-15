"""Differential layer compression stub

Provides a simple delta encoder that stores per-layer diffs relative to
the base layer. The implementation here is minimal and treats JSON-like
dictionary data as strings for diffing.
"""
from typing import List, Dict, Any


def differential_compress(base: Dict[str, Any], layers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return a list of "deltas" where delta[i] represents differences of layers[i]
    relative to base. This is a naive placeholder.
    """
    base_s = str(base)
    deltas = []
    for layer in layers:
        s = str(layer)
        if s == base_s:
            deltas.append({'type': 'same'})
        else:
            deltas.append({'type': 'full', 'data': layer})
    return deltas
