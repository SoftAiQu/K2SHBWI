"""
Tests for error handling in K2SHBWI format
"""

import os
import tempfile
from pathlib import Path
import pytest
from datetime import datetime, UTC

from src.core.encoder import K2SHBWIEncoder
from src.core.decoder import K2SHBWIDecoder
from src.core.format_spec import (
    K2SHBWIHeader,
    CompressionType,
    ValidationError,
    FormatError,
    CompressionError,
    MAGIC_BYTES,
    HEADER_SIZE
)

ASSETS_DIR = Path(__file__).parent / 'assets'
SAMPLE_IMAGE = ASSETS_DIR / 'sample.png'

def create_basic_test_file():
    """Creates a basic valid K2SHBWI file for testing"""
    enc = K2SHBWIEncoder()
    enc.set_image(str(SAMPLE_IMAGE))
    enc.add_metadata({
        'title': 'Test File',
        'author': 'Tester',
        'created_date': datetime.now(UTC).isoformat()
    })
    
    out_file = Path(tempfile.gettempdir()) / 'test_base.k2sh'
    enc.encode(str(out_file))
    return out_file

def create_corrupt_file(corruption_type: str, **kwargs):
    """Creates a corrupted K2SHBWI file based on corruption_type"""
    base_file = create_basic_test_file()
    corrupt_file = Path(tempfile.gettempdir()) / f'test_corrupt_{corruption_type}.k2sh'
    
    with open(base_file, 'rb') as src, open(corrupt_file, 'wb') as dst:
        data = bytearray(src.read())
        
        if corruption_type == 'truncated_header':
            # Write only part of the header
            dst.write(data[:HEADER_SIZE-10])
            
        elif corruption_type == 'wrong_magic':
            # Modify magic bytes
            data[0:4] = b'BAD!'
            dst.write(data)
            
        elif corruption_type == 'invalid_compression':
            # Find the metadata compression type byte and set it to an invalid value
            # Header is 56 bytes, then 4 bytes for length, then compression type
            data[HEADER_SIZE + 4] = 255  # Invalid compression type
            dst.write(data)
            
        elif corruption_type == 'truncated_section':
            # Write header and partial metadata section
            section_start = HEADER_SIZE
            section_length = int.from_bytes(data[section_start:section_start+4], 'little')
            dst.write(data[:section_start + 4 + section_length - 10])  # Truncate 10 bytes from end
    
    return corrupt_file

@pytest.fixture(scope='function')
def corrupt_file():
    """Fixture that provides a function to create corrupt test files"""
    files = []
    
    def _create_corrupt(corruption_type: str, **kwargs):
        f = create_corrupt_file(corruption_type, **kwargs)
        files.append(f)
        return f
    
    yield _create_corrupt
    
    # Cleanup files after test
    for f in files:
        try:
            f.unlink()
        except Exception:
            pass

def test_truncated_header(corrupt_file):
    """Test handling of truncated header"""
    test_file = corrupt_file('truncated_header')
    dec = K2SHBWIDecoder()
    
    with pytest.raises(ValidationError, match="Header too small"):
        dec.decode(str(test_file))

def test_truncated_section(corrupt_file):
    """Test handling of truncated metadata section"""
    test_file = corrupt_file('truncated_section')
    dec = K2SHBWIDecoder()
    
    with pytest.raises(FormatError, match="incomplete or truncated stream"):
        dec.decode(str(test_file))

def test_invalid_magic_bytes(corrupt_file):
    """Test handling of invalid magic bytes in header"""
    test_file = corrupt_file('wrong_magic')
    dec = K2SHBWIDecoder()
    
    with pytest.raises(ValidationError, match="Invalid magic bytes"):
        dec.decode(str(test_file))

def test_invalid_compression_type(corrupt_file):
    """Test handling of invalid compression type value"""
    test_file = corrupt_file('invalid_compression')
    dec = K2SHBWIDecoder()
    
    with pytest.raises(FormatError, match="is not a valid CompressionType"):
        dec.decode(str(test_file))