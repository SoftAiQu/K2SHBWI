"""Tests for algorithm selection and registration."""

import pytest
from src.algorithms.registry import registry, init_registry
from src.core.algorithm_selector import get_compression_pair

def test_registry_initialization():
    """Test that the registry initializes with expected algorithms."""
    init_registry()
    algos = registry.list_compression_algos()
    assert "smart" in algos, "Smart compression should be available"

def test_get_compression_functions():
    """Test retrieving compression functions from registry."""
    init_registry()
    compress, decompress = get_compression_pair("smart")
    
    # Test roundtrip with smart compression
    test_data = b"Hello, World!"
    compressed = compress(test_data)
    decompressed = decompress(compressed)
    assert decompressed == test_data, "Compression roundtrip should preserve data"

def test_invalid_algorithm():
    """Test that requesting an invalid algorithm raises ValueError."""
    init_registry()
    with pytest.raises(ValueError):
        get_compression_pair("nonexistent_algo")