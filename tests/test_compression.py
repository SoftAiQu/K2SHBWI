"""
Compression Algorithm Test Suite with Real-Time Logging

Tests all compression backends with detailed metrics logging:
- Input/output sizes
- Compression ratios
- Processing times
- Success/failure status

Metrics are logged to /logs/test_runs/ when run with pytest --log flag.
"""
import pytest
import time

from src.core.format_spec import CompressionType, CompressionError
from src.core.compression import compress_bytes, decompress_bytes
from src.utils.test_logger import TestLogger

# Logger instance (created once per test session)
_logger = None


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """Initialize logging for this test session"""
    global _logger
    _logger = TestLogger(logger_name="test_compression", log_type="test")
    
    yield  # Run all tests
    
    # Save logs after all tests complete
    if _logger:
        _logger.add_summary({
            "test_module": "test_compression",
            "compression_types_tested": 5,
            "benchmark_type": "roundtrip_compression_decompression"
        })
        log_paths = _logger.save_log()
        print(f"\n[Logging] Test metrics saved to {log_paths['json']}")


@pytest.mark.parametrize('ctype', [
    CompressionType.NONE,
    CompressionType.ZLIB,
    CompressionType.BROTLI,
    CompressionType.LZMA,
    CompressionType.ZSTD,
])
def test_compress_decompress_roundtrip(ctype):
    """Test compression and decompression roundtrip with detailed metrics logging"""
    data = (b'K2SHBWI-test-' * 1000)
    original_size = len(data)
    
    try:
        # Compression with timing
        start_time = time.perf_counter()
        comp = compress_bytes(ctype, data)
        compression_time_ms = (time.perf_counter() - start_time) * 1000
        
        compressed_size = len(comp)
        compression_ratio = 100.0 - (compressed_size / original_size * 100)
        
        # Decompression with timing
        start_time = time.perf_counter()
        out = decompress_bytes(ctype, comp)
        decompression_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify roundtrip
        assert out == data, f"Decompressed data doesn't match original"
        
        # Log metrics if logger is available
        if _logger:
            _logger.log_test_result(
                test_name=f"test_compress_decompress_roundtrip[{ctype.name}]",
                status="PASS",
                input_bytes=original_size,
                output_bytes=compressed_size,
                processing_time_ms=compression_time_ms + decompression_time_ms,
                compression_type=ctype.name,
                error_msg=None
            )
        
    except CompressionError as e:
        # Log failure metrics
        if _logger:
            _logger.log_test_result(
                test_name=f"test_compress_decompress_roundtrip[{ctype.name}]",
                status="SKIP",
                input_bytes=original_size,
                output_bytes=0,
                processing_time_ms=0.0,
                compression_type=ctype.name,
                error_msg=f"Compression backend not available for {ctype.name}: {e}"
            )
        # Optional libraries may be missing (brotli, zstandard). Skip in that case.
        pytest.skip(f"Compression backend not available for {ctype.name}: {e}")
