"""Semantic layer grouping stub

Placeholder implementation for semantic clustering of layers.
"""
from typing import List, Dict, Any


def group_layers(layers: List[Dict[str, Any]], n_groups: int = 2) -> List[List[int]]:
    """Return grouping of layer indices into n_groups.

    This naive stub does round-robin grouping by index.
    """
    groups = [[] for _ in range(n_groups)]
    for idx, _ in enumerate(layers):
        groups[idx % n_groups].append(idx)
    return groups
