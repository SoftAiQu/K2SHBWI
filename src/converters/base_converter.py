"""
Base converter class for K2SHBWI format conversions
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
import json
import io
from PIL import Image

from ..core.decoder import K2SHBWIDecoder


class BaseConverter(ABC):
    """Abstract base class for K2SHBWI converters"""
    
    def __init__(self):
        """Initialize converter"""
        self.decoder = K2SHBWIDecoder()
        self.stats = {}
    
    def convert(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Convert K2SHBWI file to target format
        
        Args:
            input_path: Path to K2SHBWI file
            output_path: Path to output file
            
        Returns:
            Dictionary with conversion stats
        """
        # Decode K2SHBWI file
        self.decoder.decode(input_path)
        
        # Extract components from decoder instance attributes
        metadata = self.decoder.get_metadata()
        hotspots = self.decoder.get_hotspots()
        image_data = self.decoder.image_data
        
        if not image_data:
            raise ValueError("No image data found in K2SHBWI file")
        
        image = Image.open(io.BytesIO(image_data))
        
        # Call implementation-specific conversion
        self._convert_impl(image, metadata, hotspots, output_path)
        
        # Build stats
        self.stats = {
            'input_file': input_path,
            'output_file': output_path,
            'input_size': Path(input_path).stat().st_size,
            'output_size': Path(output_path).stat().st_size if Path(output_path).exists() else 0,
            'image_size': image.size,
            'hotspots_count': len(hotspots) if hotspots else 0,
            'metadata_keys': list(metadata.keys()) if metadata else [],
            'format': self.format_name,
        }
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return format name (e.g., 'HTML', 'PDF', 'PPTX')"""
        pass
    
    @abstractmethod
    def _convert_impl(self, image: Image.Image, metadata: Dict, hotspots: list, output_path: str):
        """
        Implementation-specific conversion logic
        
        Args:
            image: PIL Image object
            metadata: File metadata dictionary
            hotspots: List of hotspots
            output_path: Output file path
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get conversion statistics"""
        return self.stats
