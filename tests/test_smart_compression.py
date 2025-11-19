"""
Smart Adaptive Compression Test Suite with Real-Time Logging

Tests adaptive compression algorithms that select the best compression type
for different data types (text, binary, etc) with detailed metrics logging:
- Input/output sizes
- Compression ratios
- Processing times
- Compression type selected
- Success/failure status

Metrics are logged to /logs/test_runs/ when run with pytest --log flag.
"""
import pytest
import time

from src.algorithms.smart_compression import adaptive_compress, adaptive_decompress
from src.core.format_spec import CompressionType, CompressionError
from src.utils.test_logger import TestLogger

# Logger instance (created once per test session)
_logger = None


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """Initialize logging for this test session"""
    global _logger
    _logger = TestLogger(logger_name="test_smart_compression", log_type="test")
    
    yield  # Run all tests
    
    # Save logs after all tests complete
    if _logger:
        _logger.add_summary({
            "test_module": "test_smart_compression",
            "adaptive_compression_data_types": ["text", "binary"],
            "benchmark_type": "adaptive_compression"
        })
        log_paths = _logger.save_log()
        print(f"\n[Logging] Test metrics saved to {log_paths['json']}")


def test_adaptive_compress_roundtrip_text():
    """Test adaptive compression on text data with logging"""
    data = (b'This is a sample text data for compression. ' * 200)
    original_size = len(data)
    
    try:
        # Compression with timing
        start_time = time.perf_counter()
        compressed, comp_type = adaptive_compress(data, data_type='text')
        compression_time_ms = (time.perf_counter() - start_time) * 1000
        
        assert isinstance(comp_type, CompressionType), f"Expected CompressionType, got {type(comp_type)}"
        compressed_size = len(compressed)
        
        # Decompression with timing
        start_time = time.perf_counter()
        out = adaptive_decompress(compressed, comp_type)
        decompression_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify roundtrip
        assert out == data, "Decompressed data doesn't match original"
        
        # Log metrics if logger is available
        if _logger:
            _logger.log_test_result(
                test_name="test_adaptive_compress_roundtrip_text",
                status="PASS",
                input_bytes=original_size,
                output_bytes=compressed_size,
                processing_time_ms=compression_time_ms + decompression_time_ms,
                compression_type=comp_type.name,
                error_msg=None
            )
    
    except Exception as e:
        # Log failure metrics
        if _logger:
            _logger.log_test_result(
                test_name="test_adaptive_compress_roundtrip_text",
                status="FAIL",
                input_bytes=original_size,
                output_bytes=0,
                processing_time_ms=0.0,
                compression_type="UNKNOWN",
                error_msg=str(e)
            )
        raise


def test_adaptive_compress_roundtrip_binary():
    """Test adaptive compression on binary data with logging"""
    data = (b"\x00\x01\x02\x03" * 2000)
    original_size = len(data)
    
    try:
        # Compression with timing
        start_time = time.perf_counter()
        compressed, comp_type = adaptive_compress(data, data_type='binary')
        compression_time_ms = (time.perf_counter() - start_time) * 1000
        
        assert isinstance(comp_type, CompressionType), f"Expected CompressionType, got {type(comp_type)}"
        compressed_size = len(compressed)
        
        # Decompression with timing
        start_time = time.perf_counter()
        out = adaptive_decompress(compressed, comp_type)
        decompression_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify roundtrip
        assert out == data, "Decompressed data doesn't match original"
        
        # Log metrics if logger is available
        if _logger:
            _logger.log_test_result(
                test_name="test_adaptive_compress_roundtrip_binary",
                status="PASS",
                input_bytes=original_size,
                output_bytes=compressed_size,
                processing_time_ms=compression_time_ms + decompression_time_ms,
                compression_type=comp_type.name,
                error_msg=None
            )
    
    except Exception as e:
        # Log failure metrics
        if _logger:
            _logger.log_test_result(
                test_name="test_adaptive_compress_roundtrip_binary",
                status="FAIL",
                input_bytes=original_size,
                output_bytes=0,
                processing_time_ms=0.0,
                compression_type="UNKNOWN",
                error_msg=str(e)
            )
        raise
