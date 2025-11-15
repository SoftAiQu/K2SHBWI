"""
Tests for K2SHBWI encoder
"""

import pytest
from pathlib import Path
import json
from PIL import Image
import io

from src.core.encoder import K2SHBWIEncoder
from src.core.decoder import K2SHBWIDecoder

def test_basic_encoding():
    encoder = K2SHBWIEncoder()
    
    # Add test metadata
    test_metadata = {
        "title": "Test Image",
        "author": "Test Author",
        "description": "Test Description"
    }
    encoder.add_metadata(test_metadata)
    
    # Add test hotspot
    test_hotspot = {
        "coords": (100, 100, 200, 200),
        "data": {"description": "Test Hotspot"}
    }
    encoder.add_hotspot(test_hotspot["coords"], test_hotspot["data"])
    
    # Add test data layer
    test_layer = {
        "type": "information",
        "content": "Test Content"
    }
    encoder.add_data_layer("layer1", test_layer)
    
    # Test encoding
    test_output = "test_output.k2sh"
    encoder.encode(test_output)
    
    # Verify with decoder
    decoder = K2SHBWIDecoder()
    decoder.decode(test_output)
    
    assert decoder.get_metadata() == test_metadata
    assert len(decoder.get_hotspots()) == 1
    assert decoder.get_data_layer("layer1") == test_layer