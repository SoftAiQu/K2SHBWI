## File: `src/creator/builder.py`
"""
K2SHBWI Builder - High-level API for creating K2SHBWI files
"""

import os
import time
from typing import Dict, List, Any, Optional, Tuple, Callable
from PIL import Image
import json
from pathlib import Path

from ..core.encoder import K2SHBWIEncoder
from ..algorithms.multi_level_compression import MultiLevelCompressor
from ..algorithms.hotspot_detection import auto_detect_hotspots
from ..algorithms.data_optimization import minify_structure
import logging
import uuid

logger = logging.getLogger(__name__)


class K2SHBWIBuilder:
    """
    High-level builder for creating K2SHBWI files
    
    Example:
        >>> builder = K2SHBWIBuilder()
        >>> builder.set_base_image('diagram.png')
        >>> builder.add_hotspot((100, 100, 300, 300), data={'title': 'Info'})
        >>> stats = builder.build('output.k2sh')
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize builder
        
        Args:
            config: Optional configuration dictionary
        """
        self.encoder = K2SHBWIEncoder()
        self.compressor = MultiLevelCompressor()
        
        self.base_image = None
        self.base_image_path = None
        self.hotspots = []
        self.metadata = {}
        self.config = config or self._default_config()
        
        # Statistics
        self.stats = {
            'hotspots_added': 0,
            'data_layers_created': 0,
            'total_data_size': 0,
            'auto_detected_hotspots': 0
        }
    
    def _default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'compression': {
                'image_quality': 'high',
                'data_algorithm': 'adaptive',
                'enable_deduplication': True,
                'enable_differential': True,
                'enable_perceptual': True
            },
            'optimization': {
                'auto_optimize_images': True,
                'max_image_dimension': 4096,
                'remove_exif': True
            },
            'hotspots': {
                'auto_detect': False,
                'min_confidence': 0.75,
                'max_hotspots': 50
            }
        }
    
    def configure_compression(
        self,
        image_quality: str = 'high',
        data_algorithm: str = 'adaptive',
        enable_deduplication: bool = True,
        enable_differential: bool = True
    ) -> 'K2SHBWIBuilder':
        """
        Configure compression settings
        
        Args:
            image_quality: 'low', 'medium', 'high', 'ultra'
            data_algorithm: 'adaptive', 'brotli', 'lzma', 'zstd'
            enable_deduplication: Enable content deduplication
            enable_differential: Enable differential compression for similar data
            
        Returns:
            Self for chaining
        """
        self.config['compression'].update({
            'image_quality': image_quality,
            'data_algorithm': data_algorithm,
            'enable_deduplication': enable_deduplication,
            'enable_differential': enable_differential
        })
        return self
    
    def set_metadata(self, metadata: Dict[str, Any]) -> 'K2SHBWIBuilder':
        """
        Set file metadata
        
        Args:
            metadata: Dictionary containing title, author, description, tags, etc.
            
        Returns:
            Self for chaining
        """
        self.metadata = metadata
        self.encoder.add_metadata(metadata)
        return self
    
    def set_base_image(
        self,
        image_path: str,
        auto_optimize: Optional[bool] = None
    ) -> 'K2SHBWIBuilder':
        """
        Load and set base image
        
        Args:
            image_path: Path to image file
            auto_optimize: Override auto-optimization setting
            
        Returns:
            Self for chaining
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        self.base_image_path = image_path
        self.base_image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if self.base_image.mode not in ('RGB', 'RGBA'):
            self.base_image = self.base_image.convert('RGB')
        
        # Auto-optimize if enabled
        should_optimize = (
            auto_optimize if auto_optimize is not None 
            else self.config['optimization']['auto_optimize_images']
        )
        
        if should_optimize:
            self.optimize_image()
        
        self.encoder.set_image(image_path)
        
        return self
    
    def optimize_image(
        self,
        max_dimension: Optional[int] = None,
        quality: str = 'perceptual',
        remove_metadata: bool = True
    ) -> 'K2SHBWIBuilder':
        """
        Optimize base image
        
        Args:
            max_dimension: Maximum width/height (resizes if larger)
            quality: 'perceptual', 'lossless', or 'balanced'
            remove_metadata: Remove EXIF/metadata
            
        Returns:
            Self for chaining
        """
        if self.base_image is None:
            raise ValueError("No base image set")
        
        max_dim = max_dimension or self.config['optimization']['max_image_dimension']
        
        # Resize if needed
        if max(self.base_image.size) > max_dim:
            # Calculate new size maintaining aspect ratio
            w, h = self.base_image.size
            ratio = max_dim / max(w, h)
            new_size = (int(w * ratio), int(h * ratio))
            self.base_image = self.base_image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Apply perceptual optimization (quality='perceptual' would require external library)
        # For now, just keep the resized image
        if quality == 'perceptual':
            # Could apply filters here using PIL, but for now just return
            logger.debug("Perceptual optimization requested (stub - PIL filters can be added)")
        
        return self
    
    def add_hotspot(
        self,
        coords: Tuple[float, float, float, float],
        data: Dict[str, Any],
        shape: str = 'rectangle',
        visible: bool = True,
        lazy_load: bool = False,
        priority: int = 5
    ) -> str:
        """
        Add interactive hotspot
        
        Args:
            coords: (x1, y1, x2, y2) coordinates
            data: Data to associate with hotspot
            shape: 'rectangle', 'circle', 'polygon', 'ellipse'
            visible: Visible by default
            lazy_load: Load data only when clicked
            priority: Load priority (1=highest, 10=lowest)
            
        Returns:
            hotspot_id (UUID string)
        """
        # Validate coordinates
        x1, y1, x2, y2 = coords
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"Invalid coordinates: {coords}")
        
        # Validate shape
        valid_shapes = ['rectangle', 'circle', 'polygon', 'ellipse']
        if shape not in valid_shapes:
            raise ValueError(f"Invalid shape. Must be one of: {valid_shapes}")
        
        # Optimize data (minify JSON for storage)
        optimized_data = minify_structure(data) if isinstance(data, dict) else data
        
        # Store shape and metadata in data dict for later retrieval
        hotspot_data = {
            'shape': shape,
            'visible': visible,
            'lazy_load': lazy_load,
            'priority': priority,
            'user_data': data
        }
        
        # Generate an id and add to hotspot data so encoder stores it with the hotspot
        hotspot_id = str(uuid.uuid4())
        hotspot_data['id'] = hotspot_id

        # Add to encoder (only accepts coords and data)
        # encoder.add_hotspot does not return an id, so we pass the id in data
        self.encoder.add_hotspot(
            coords=coords,
            data=hotspot_data
        )

        # Track statistics
        self.stats['hotspots_added'] += 1
        self.stats['data_layers_created'] += 1
        self.stats['total_data_size'] += len(json.dumps(data).encode())

        # Store for later reference
        self.hotspots.append({
            'id': hotspot_id,
            'coords': coords,
            'data': optimized_data,
            'shape': shape,
            'priority': priority
        })

        return hotspot_id
    
    def add_hotspots_batch(
        self,
        hotspots: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Add multiple hotspots at once
        
        Args:
            hotspots: List of hotspot dictionaries with coords, data, etc.
            
        Returns:
            List of hotspot IDs
        """
        ids = []
        for hotspot in hotspots:
            hotspot_id = self.add_hotspot(
                coords=hotspot['coords'],
                data=hotspot['data'],
                shape=hotspot.get('shape', 'rectangle'),
                visible=hotspot.get('visible', True),
                lazy_load=hotspot.get('lazy_load', False),
                priority=hotspot.get('priority', 5)
            )
            ids.append(hotspot_id)
        
        return ids
    
    def auto_detect_hotspots(
        self,
        min_confidence: Optional[float] = None,
        max_hotspots: Optional[int] = None,
        review_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Automatically detect hotspots using AI
        
        Args:
            min_confidence: Minimum confidence threshold (0.0-1.0)
            max_hotspots: Maximum number of hotspots to detect
            review_callback: Optional callback for manual review
            
        Returns:
            List of detected hotspot suggestions
        """
        if self.base_image is None:
            raise ValueError("No base image set")
        
        min_conf = min_confidence or self.config['hotspots']['min_confidence']
        max_hs = max_hotspots or self.config['hotspots']['max_hotspots']
        
        # Detect hotspots using the auto_detect function (currently a stub returning empty list)
        if self.base_image_path:
            with open(self.base_image_path, 'rb') as f:
                image_bytes = f.read()
            suggestions = auto_detect_hotspots(image_bytes)
        else:
            # If no path, convert in-memory image to bytes
            import io
            img_bytes_io = io.BytesIO()
            self.base_image.save(img_bytes_io, format='PNG')
            suggestions = auto_detect_hotspots(img_bytes_io.getvalue())
        
        self.stats['auto_detected_hotspots'] = len(suggestions)
        
        # Optional manual review
        if review_callback:
            suggestions = [s for s in suggestions if review_callback(s)]
        
        return suggestions
    
    def apply_suggested_hotspots(
        self,
        suggestions: List[Dict],
           data_generator: Optional[Callable] = None
    ) -> List[str]:
        """
        Apply suggested hotspots from auto-detection
        
        Args:
            suggestions: List from auto_detect_hotspots()
            data_generator: Optional function to generate data for each hotspot
            
        Returns:
            List of created hotspot IDs
        """
        ids = []
        
        for suggestion in suggestions:
            # Generate or use placeholder data
            if data_generator:
                data = data_generator(suggestion)
            else:
                data = {
                    'title': f"{suggestion.get('type', 'Region').title()}",
                    'description': f"Auto-detected {suggestion.get('type', 'region')}",
                    'confidence': suggestion.get('confidence', 0.0),
                    'metadata': suggestion.get('metadata', {})
                }
            
            hotspot_id = self.add_hotspot(
                coords=suggestion['coords'],
                data=data,
                shape=suggestion.get('shape', 'rectangle')
            )
            ids.append(hotspot_id)
        
        return ids
    
    def update_hotspot(
        self,
        hotspot_id: str,
        coords: Optional[Tuple] = None,
        data: Optional[Dict] = None,
        **kwargs
    ) -> bool:
        """
        Update existing hotspot
        
        Args:
            hotspot_id: ID of hotspot to update
            coords: New coordinates (optional)
            data: New data (optional)
            **kwargs: Other properties to update
            
        Returns:
            True if updated successfully
        """
        # Find hotspot
        hotspot = next((h for h in self.hotspots if h['id'] == hotspot_id), None)
        if not hotspot:
            return False
        
        # Update properties
        if coords:
            hotspot['coords'] = coords
        if data:
               hotspot['data'] = minify_structure(data) if isinstance(data, dict) else data
        
        for key, value in kwargs.items():
            if key in hotspot:
                hotspot[key] = value
        
        return True
    
    def remove_hotspot(self, hotspot_id: str) -> bool:
        """
        Remove hotspot
        
        Args:
            hotspot_id: ID of hotspot to remove
            
        Returns:
            True if removed successfully
        """
        initial_count = len(self.hotspots)
        self.hotspots = [h for h in self.hotspots if h['id'] != hotspot_id]
        return len(self.hotspots) < initial_count
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate current configuration before building
        
        Returns:
            Validation results with errors/warnings
        """
        errors = []
        warnings = []
        
        # Check base image
        if self.base_image is None:
            errors.append("No base image set")
        else:
            w, h = self.base_image.size
            if w < 256 or h < 256:
                warnings.append(f"Image very small ({w}x{h}), recommend 512x512+")
            if w > 8192 or h > 8192:
                warnings.append(f"Image very large ({w}x{h}), will be resized")
        
        # Check hotspots
        if len(self.hotspots) == 0:
            warnings.append("No hotspots defined - file will be static image only")
        
        if len(self.hotspots) > 100:
            warnings.append(f"{len(self.hotspots)} hotspots may impact performance")
        
        # Check data sizes
        for i, hotspot in enumerate(self.hotspots):
            data_size = len(json.dumps(hotspot['data']).encode())
            if data_size > 1_000_000:  # 1MB
                warnings.append(
                    f"Hotspot {i+1} has large data ({data_size/1024:.1f}KB), "
                    "consider lazy loading"
                )
        
        # Check metadata
        if not self.metadata:
            warnings.append("No metadata set - recommend adding title/author")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def build(
        self,
        output_path: str,
        validate: bool = True,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Build K2SHBWI file
        
        Args:
            output_path: Output file path (.k2sh)
            validate: Run validation before building
            verbose: Print progress messages
            
        Returns:
            Statistics dictionary with build info
        """
        if verbose:
            print("🚀 Building K2SHBWI file...")
            print()
        
        # Validate
        if validate:
            if verbose:
                print("📋 Validating configuration...")
            
            validation = self.validate()
            
            if not validation['valid']:
                raise ValueError(
                    f"Validation failed:\n" + 
                    "\n".join(f"  ❌ {e}" for e in validation['errors'])
                )
            
            if validation['warnings'] and verbose:
                for warning in validation['warnings']:
                    print(f"  ⚠️  {warning}")
                print()
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Add extension if missing
        if not output_path.endswith('.k2sh'):
            output_path += '.k2sh'
        
        # Build using encoder
        if verbose:
            print("🔧 Encoding file...")
        
        start_time = time.time()
        self.encoder.encode(output_path)
        build_time = time.time() - start_time

        # Add additional statistics
        stats = {
            'hotspots_count': len(self.hotspots),
            'build_time': build_time,
            'output_path': output_path,
            'output_size_mb': os.path.getsize(output_path) / (1024 * 1024) if os.path.exists(output_path) else 0,
            'compression_ratio_percent': 100
        }
        
        if verbose:
            print()
            print("✅ Build complete!")
            print()
            print(f"📄 File: {output_path}")
            print(f"📊 Size: {stats['output_size_mb']:.2f} MB")
            print(f"🗜️  Compression: {stats['compression_ratio_percent']:.1f}%")
            print(f"🎯 Hotspots: {stats['hotspots_count']}")
            print(f"⏱️  Time: {build_time:.2f}s")
            print()
        
        return stats
    
    def preview(self) -> Dict[str, Any]:
        """
        Generate preview information without building file
        
        Returns:
            Preview dictionary with estimated stats
        """
        if self.base_image is None:
            raise ValueError("No base image set")
        
        # Estimate sizes
        image_size = len(self.base_image.tobytes())
        data_size = sum(
            len(json.dumps(h['data']).encode())
            for h in self.hotspots
        )
        
        # Estimate compression (conservative)
        estimated_image = image_size * 0.15  # ~85% compression
        estimated_data = data_size * 0.25    # ~75% compression
        estimated_total = estimated_image + estimated_data + 10240  # +10KB overhead
        
        return {
            'base_image_size': self.base_image.size,
            'hotspots_count': len(self.hotspots),
            'estimated_size_bytes': int(estimated_total),
            'estimated_size_mb': estimated_total / (1024 * 1024),
            'image_contribution_percent': (estimated_image / estimated_total) * 100,
            'data_contribution_percent': (estimated_data / estimated_total) * 100
        }
    
    def export_json(self, output_path: str) -> None:
        """
        Export configuration as JSON (for debugging/backup)
        
        Args:
            output_path: Path to JSON file
        """
        export_data = {
            'metadata': self.metadata,
            'config': self.config,
            'base_image': self.base_image_path,
            'hotspots': self.hotspots,
            'stats': self.stats
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def import_json(self, input_path: str) -> 'K2SHBWIBuilder':
        """
        Import configuration from JSON
        
        Args:
            input_path: Path to JSON file
            
        Returns:
            Self for chaining
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'metadata' in data:
            self.set_metadata(data['metadata'])
        
        if 'config' in data:
            self.config = data['config']
        
        if 'base_image' in data and data['base_image']:
            self.set_base_image(data['base_image'])
        
        if 'hotspots' in data:
            for hotspot in data['hotspots']:
                self.add_hotspot(
                    coords=tuple(hotspot['coords']),
                    data=hotspot['data'],
                    shape=hotspot.get('shape', 'rectangle'),
                    priority=hotspot.get('priority', 5)
                )
        
        return self