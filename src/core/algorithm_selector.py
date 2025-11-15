"""Module for enforcing encoder algorithm selection via registry."""

from ..algorithms.registry import registry

def get_compression_pair(algorithm_name=None):
    """Get compression/decompression functions for the named algorithm."""
    return registry.get_compression(algorithm_name)