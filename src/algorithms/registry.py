"""
Algorithm registry for K2SHBWI compression algorithms.
"""
from typing import Callable, Dict, List, Optional, Tuple, Any
import importlib
from PIL import Image
from ..core.format import CompressionType

# Type hints for compression functions
# Raw compression functions work directly with bytes
RawCompressFunc = Callable[[bytes], bytes]
RawDecompressFunc = Callable[[bytes], bytes]
# Algorithm-specific functions may have additional parameters
ImageAlgoFunc = Callable[[Image.Image], Tuple[bytes, dict]]

class AlgorithmRegistry:
    """Central registry for compression algorithms."""
    
    def __init__(self):
        self._compression_algos: Dict[str, Tuple[RawCompressFunc, RawDecompressFunc]] = {}
        self._image_algos: Dict[str, Tuple[Any, Any]] = {}  # Store original functions
        self._default_compression = "smart"  # Use smart_compression by default
        self._default_image = "adaptive"     # Use adaptive image compression by default
    
    def register_compression(self, name: str, compress_func: RawCompressFunc, 
                           decompress_func: RawDecompressFunc) -> None:
        """Register a pair of compression/decompression functions."""
        self._compression_algos[name] = (compress_func, decompress_func)
    
    def register_image_algo(self, name: str, process_func: ImageAlgoFunc) -> None:
        """Register an image processing algorithm."""
        self._image_algos[name] = process_func
    
    def get_compression(self, name: Optional[str] = None) -> Tuple[RawCompressFunc, RawDecompressFunc]:
        """Get compression functions by name, or default if None."""
        name = name or self._default_compression
        if name not in self._compression_algos:
            raise ValueError(f"Unknown compression algorithm: {name}")
        return self._compression_algos[name]
    
    def get_image_algo(self, name: Optional[str] = None) -> ImageAlgoFunc:
        """Get image algorithm by name, or default if None."""
        name = name or self._default_image
        if name not in self._image_algos:
            raise ValueError(f"Unknown image algorithm: {name}")
        return self._image_algos[name]
    
    def list_compression_algos(self) -> List[str]:
        """List available compression algorithms."""
        return sorted(self._compression_algos.keys())
    
    def list_image_algos(self) -> List[str]:
        """List available image algorithms."""
        return sorted(self._image_algos.keys())
    
    def set_default_compression(self, name: str) -> None:
        """Set the default compression algorithm."""
        if name not in self._compression_algos:
            raise ValueError(f"Unknown compression algorithm: {name}")
        self._default_compression = name
    
    def set_default_image(self, name: str) -> None:
        """Set the default image algorithm."""
        if name not in self._image_algos:
            raise ValueError(f"Unknown image algorithm: {name}")
        self._default_image = name

# Global registry instance
registry = AlgorithmRegistry()

def init_registry():
    """Initialize the registry with all available algorithms."""
    from .smart_compression import adaptive_compress, adaptive_decompress
    
    # Create wrappers for smart compression to match the simple bytes->bytes API
    def smart_compress_wrapper(data: bytes) -> bytes:
        compressed, comp_type = adaptive_compress(data)
        # Store compression type in a header byte
        return bytes([comp_type.value]) + compressed
    
    def smart_decompress_wrapper(data: bytes) -> bytes:
        # Extract compression type from header byte
        comp_type = CompressionType(data[0])
        return adaptive_decompress(data[1:], comp_type)
    
    registry.register_compression("smart", smart_compress_wrapper, smart_decompress_wrapper)
    
    # Import and register all other algorithms
    algo_modules = [
        "basic_compression", "enhanced_compression", "lossy_compression",
        "lossless_compression", "predictive_compression", "dictionary_compression",
        "arithmetic_compression", "huffman_compression", "lzw_compression",
        "rle_compression", "delta_compression", "probability_compression",
        "transform_compression", "wavelet_compression", "fractal_compression"
    ]
    
    for module_name in algo_modules:
        try:
            module = importlib.import_module(f".{module_name}", package="k2shbwi.algorithms")
            if hasattr(module, "compress") and hasattr(module, "decompress"):
                registry.register_compression(
                    module_name.replace("_compression", ""),
                    module.compress,
                    module.decompress
                )
        except ImportError:
            continue  # Skip unavailable algorithms