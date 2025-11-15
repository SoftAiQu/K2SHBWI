"""
Content Validation for K2SHBWI Files
"""

from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import json
import re


class ValidationError:
    """Represents a validation error"""
    
    def __init__(
        self,
        level: str,
        message: str,
        field: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        self.level = level  # 'error', 'warning', 'info'
        self.message = message
        self.field = field
        self.suggestion = suggestion
    
    def __repr__(self):
        prefix = {
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        }.get(self.level, '•')
        
        field_str = f" [{self.field}]" if self.field else ""
        return f"{prefix} {self.message}{field_str}"


class K2SHBWIValidator:
    """
    Validates K2SHBWI content before encoding
    """
    
    def __init__(self):
        """Initialize validator"""
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.info: List[ValidationError] = []
    
    def validate_all(
        self,
        image: Optional[Image.Image],
        hotspots: List[Dict],
        metadata: Dict,
        config: Dict
    ) -> bool:
        """
        Validate all components
        
        Returns:
            True if valid (no errors), False otherwise
        """
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()
        
        # Validate image
        if image:
            self.validate_image(image)
        else:
            self.add_error("No base image provided")
        
        # Validate hotspots
        if image:
            self.validate_hotspots(hotspots, image.size)
        
        # Validate metadata
        self.validate_metadata(metadata)
        
        # Validate configuration
        self.validate_config(config)
        
        return len(self.errors) == 0
    
    def validate_image(self, image: Image.Image) -> None:
        """Validate base image"""
        width, height = image.size
        
        # Check minimum size
        if width < 256 or height < 256:
            self.add_error(
                f"Image too small ({width}x{height}). Minimum 256x256 recommended.",
                field="image",
                suggestion="Use a higher resolution image"
            )
        
        # Check maximum size
        if width > 8192 or height > 8192:
            self.add_warning(
                f"Image very large ({width}x{height}). Will be resized to max 4096x4096.",
                field="image",
                suggestion="Pre-resize image for better control"
            )
        
        # Check aspect ratio
        aspect_ratio = width / height
        if aspect_ratio > 5 or aspect_ratio < 0.2:
            self.add_warning(
                f"Unusual aspect ratio ({aspect_ratio:.2f}:1). May display oddly.",
                field="image"
            )
        
        # Check mode
        if image.mode not in ('RGB', 'RGBA', 'L'):
            self.add_warning(
                f"Image mode '{image.mode}' will be converted to RGB.",
                field="image"
            )
        
        # Estimate file size
        estimated_size = (width * height * 3) / (1024 * 1024)  # MB
        if estimated_size > 20:
            self.add_info(
                f"Large image (~{estimated_size:.1f}MB uncompressed). "
                "Compression will reduce this significantly.",
                field="image"
            )
    
    def validate_hotspots(
        self,
        hotspots: List[Dict],
        image_size: Tuple[int, int]
    ) -> None:
        """Validate hotspots"""
        img_width, img_height = image_size
        
        # Check if any hotspots exist
        if len(hotspots) == 0:
            self.add_warning(
                "No hotspots defined. File will be a static image only.",
                field="hotspots",
                suggestion="Add at least one hotspot for interactivity"
            )
            return
        
        # Check maximum count
        if len(hotspots) > 100:
            self.add_warning(
                f"{len(hotspots)} hotspots is quite many. May impact performance.",
                field="hotspots",
                suggestion="Consider grouping related content"
            )
        
        # Validate each hotspot
        for i, hotspot in enumerate(hotspots):
            self.validate_single_hotspot(hotspot, i, image_size)
        
        # Check for overlaps
        overlaps = self.find_hotspot_overlaps(hotspots)
        if overlaps:
            self.add_info(
                f"{len(overlaps)} hotspot overlaps detected.",
                field="hotspots",
                suggestion="Overlapping hotspots may confuse users"
            )
    
    def validate_single_hotspot(
        self,
        hotspot: Dict,
        index: int,
        image_size: Tuple[int, int]
    ) -> None:
        """Validate individual hotspot"""
        img_width, img_height = image_size
        
        # Check required fields
        if 'coords' not in hotspot:
            self.add_error(
                f"Hotspot {index+1} missing 'coords' field",
                field=f"hotspots[{index}]"
            )
            return
        
        if 'data' not in hotspot:
            self.add_error(
                f"Hotspot {index+1} missing 'data' field",
                field=f"hotspots[{index}]"
            )
            return
        
        # Validate coordinates
        coords = hotspot['coords']
        if len(coords) != 4:
            self.add_error(
                f"Hotspot {index+1} has invalid coords (expected 4 values)",
                field=f"hotspots[{index}].coords"
            )
            return
        
        x1, y1, x2, y2 = coords
        
        # Check coordinate validity
        if x1 >= x2 or y1 >= y2:
            self.add_error(
                f"Hotspot {index+1} has invalid coordinates (x1={x1}, y1={y1}, x2={x2}, y2={y2})",
                field=f"hotspots[{index}].coords",
                suggestion="Ensure x1 < x2 and y1 < y2"
            )
        
        # Check if within image bounds
        if x1 < 0 or y1 < 0 or x2 > img_width or y2 > img_height:
            self.add_warning(
                f"Hotspot {index+1} extends outside image bounds",
                field=f"hotspots[{index}].coords"
            )
        
        # Check size
        width = x2 - x1
        height = y2 - y1
        area = width * height
        
        if area < 100:  # 10x10 pixels
            self.add_warning(
                f"Hotspot {index+1} is very small ({area:.0f}px²). May be hard to click.",
                field=f"hotspots[{index}].coords",
                suggestion="Make hotspot at least 20x20 pixels"
            )
        
        # Validate data
        data = hotspot['data']
        if not isinstance(data, dict):
            self.add_error(
                f"Hotspot {index+1} data must be a dictionary",
                field=f"hotspots[{index}].data"
            )
        else:
            self.validate_hotspot_data(data, index)
    
    def validate_hotspot_data(self, data: Dict, hotspot_index: int) -> None:
        """Validate hotspot data content"""
        # Check data size
        data_json = json.dumps(data)
        data_size = len(data_json.encode())
        
        if data_size > 1_000_000:  # 1MB
            self.add_warning(
                f"Hotspot {hotspot_index+1} has large data ({data_size/1024:.1f}KB)",
                field=f"hotspots[{hotspot_index}].data",
                suggestion="Consider enabling lazy loading for this hotspot"
            )
        
        # Check for recommended fields
        recommended_fields = ['title', 'description']
        missing_fields = [f for f in recommended_fields if f not in data]
        
        if missing_fields:
            self.add_info(
                f"Hotspot {hotspot_index+1} missing recommended fields: {', '.join(missing_fields)}",
                field=f"hotspots[{hotspot_index}].data"
            )
        
        # Check for very nested data
        max_depth = self.get_dict_depth(data)
        if max_depth > 10:
            self.add_warning(
                f"Hotspot {hotspot_index+1} has deeply nested data (depth {max_depth})",
                field=f"hotspots[{hotspot_index}].data",
                suggestion="Consider flattening data structure"
            )
    
    def validate_metadata(self, metadata: Dict) -> None:
        """Validate metadata"""
        # Check for recommended fields
        recommended_fields = {
            'title': 'Give your content a descriptive title',
            'author': 'Add author information',
            'description': 'Add a brief description',
            'tags': 'Add tags for searchability'
        }
        
        for field, suggestion in recommended_fields.items():
            if field not in metadata or not metadata[field]:
                self.add_info(
                    f"Metadata missing '{field}' field",
                    field=f"metadata.{field}",
                    suggestion=suggestion
                )
        
        # Validate title
        if 'title' in metadata:
            title = metadata['title']
            if len(title) > 200:
                self.add_warning(
                    f"Title is very long ({len(title)} characters)",
                    field="metadata.title",
                    suggestion="Keep title under 100 characters"
                )
        
        # Validate tags
        if 'tags' in metadata:
            tags = metadata['tags']
            if not isinstance(tags, list):
                self.add_warning(
                    "Tags should be a list",
                    field="metadata.tags"
                )
            elif len(tags) > 20:
                self.add_info(
                    f"{len(tags)} tags is quite many",
                    field="metadata.tags",
                    suggestion="Use 5-10 most relevant tags"
                )
    
    def validate_config(self, config: Dict) -> None:
        """Validate configuration"""
        # Check compression settings
        if 'compression' in config:
            comp = config['compression']
            
            valid_qualities = ['low', 'medium', 'high', 'ultra']
            if 'image_quality' in comp and comp['image_quality'] not in valid_qualities:
                self.add_error(
                    f"Invalid image_quality '{comp['image_quality']}'",
                    field="config.compression.image_quality",
                    suggestion=f"Must be one of: {', '.join(valid_qualities)}"
                )
            
            valid_algorithms = ['adaptive', 'brotli', 'lzma', 'zstd', 'zlib']
            if 'data_algorithm' in comp and comp['data_algorithm'] not in valid_algorithms:
                self.add_error(
                    f"Invalid data_algorithm '{comp['data_algorithm']}'",
                    field="config.compression.data_algorithm",
                    suggestion=f"Must be one of: {', '.join(valid_algorithms)}"
                )
    
    def find_hotspot_overlaps(self, hotspots: List[Dict]) -> List[Tuple[int, int]]:
        """
        Find overlapping hotspots
        
        Returns:
            List of (index1, index2) tuples for overlapping pairs
        """
        overlaps = []
        
        for i, hotspot1 in enumerate(hotspots):
            if 'coords' not in hotspot1:
                continue
            
            x1a, y1a, x2a, y2a = hotspot1['coords']
            
            for j, hotspot2 in enumerate(hotspots[i+1:], start=i+1):
                if 'coords' not in hotspot2:
                    continue
                
                x1b, y1b, x2b, y2b = hotspot2['coords']
                
                # Check if rectangles overlap
                if not (x2a < x1b or x2b < x1a or y2a < y1b or y2b < y1a):
                    overlaps.append((i, j))
        
        return overlaps
    
    def get_dict_depth(self, d: Any, depth: int = 0) -> int:
        """Calculate maximum depth of nested dictionary"""
        if not isinstance(d, dict):
            return depth
        
        if not d:
            return depth + 1
        
        return max(self.get_dict_depth(v, depth + 1) for v in d.values())
    
    def add_error(
        self,
        message: str,
        field: Optional[str] = None,
        suggestion: Optional[str] = None
    ) -> None:
        """Add error"""
        self.errors.append(ValidationError('error', message, field, suggestion))
    
    def add_warning(
        self,
        message: str,
        field: Optional[str] = None,
        suggestion: Optional[str] = None
    ) -> None:
        """Add warning"""
        self.warnings.append(ValidationError('warning', message, field, suggestion))
    
    def add_info(
        self,
        message: str,
        field: Optional[str] = None,
        suggestion: Optional[str] = None
    ) -> None:
        """Add info"""
        self.info.append(ValidationError('info', message, field, suggestion))
    
    def get_report(self, include_info: bool = True) -> str:
        """
        Generate validation report
        
        Args:
            include_info: Include info messages
            
        Returns:
            Formatted report string
        """
        lines = []
        
        lines.append("=" * 60)
        lines.append("K2SHBWI VALIDATION REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        # Summary
        total_issues = len(self.errors) + len(self.warnings)
        if include_info:
            total_issues += len(self.info)
        
        if total_issues == 0:
            lines.append("✅ No issues found!")
        else:
            lines.append(f"Found {total_issues} issue(s):")
            lines.append(f"  • Errors: {len(self.errors)}")
            lines.append(f"  • Warnings: {len(self.warnings)}")
            if include_info:
                lines.append(f"  • Info: {len(self.info)}")
        
        lines.append("")
        
        # Errors
        if self.errors:
            lines.append("ERRORS (Must Fix):")
            lines.append("-" * 60)
            for error in self.errors:
                lines.append(str(error))
                if error.suggestion:
                    lines.append(f"  💡 Suggestion: {error.suggestion}")
            lines.append("")
        
        # Warnings
        if self.warnings:
            lines.append("WARNINGS (Should Fix):")
            lines.append("-" * 60)
            for warning in self.warnings:
                lines.append(str(warning))
                if warning.suggestion:
                    lines.append(f"  💡 Suggestion: {warning.suggestion}")
            lines.append("")
        
        # Info
        if include_info and self.info:
            lines.append("INFO (Optional):")
            lines.append("-" * 60)
            for info in self.info:
                lines.append(str(info))
                if info.suggestion:
                    lines.append(f"  💡 Suggestion: {info.suggestion}")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)"""
        return len(self.errors) == 0