## File: `src/creator/hotspot_mapper.py`
"""
Hotspot Mapping and Management
"""

from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from dataclasses import dataclass
import uuid


@dataclass
class Hotspot:
    """Represents a single hotspot"""
    id: str
    coords: Any  # rectangle: (x1, y1, x2, y2), circle: (cx, cy, radius, _), or polygon: List[Tuple[float, float]]
    shape: str
    data: Dict[str, Any]
    visible: bool = True
    clickable: bool = True
    hoverable: bool = False
    lazy_load: bool = False
    priority: int = 5
    layer_index: int = 0
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within hotspot"""
        if self.shape == 'rectangle':
            x1, y1, x2, y2 = self.coords
            return x1 <= x <= x2 and y1 <= y <= y2
        
        elif self.shape == 'circle':
            cx, cy, radius, _ = self.coords
            distance = ((x - cx)**2 + (y - cy)**2)**0.5
            return distance <= radius
        
        elif self.shape == 'polygon':
            # Point-in-polygon test (ray casting algorithm)
            return self._point_in_polygon(x, y, self.coords)
        
        return False
    
    def _point_in_polygon(self, x: float, y: float, polygon: List[Tuple]) -> bool:
        """Ray casting algorithm for point-in-polygon test"""
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def overlaps_with(self, other: 'Hotspot') -> bool:
        """Check if this hotspot overlaps with another"""
        if self.shape == 'rectangle' and other.shape == 'rectangle':
            x1a, y1a, x2a, y2a = self.coords
            x1b, y1b, x2b, y2b = other.coords
            
            return not (x2a < x1b or x2b < x1a or y2a < y1b or y2b < y1a)
        
        # For other shapes, use bounding box approximation
        return self._bounding_boxes_overlap(other)
    
    def _bounding_boxes_overlap(self, other: 'Hotspot') -> bool:
        """Check if bounding boxes overlap"""
        bbox1 = self.get_bounding_box()
        bbox2 = other.get_bounding_box()
        
        x1a, y1a, x2a, y2a = bbox1
        x1b, y1b, x2b, y2b = bbox2
        
        return not (x2a < x1b or x2b < x1a or y2a < y1b or y2b < y1a)
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """Get bounding box (x1, y1, x2, y2)"""
        if self.shape == 'rectangle':
            return self.coords
        
        elif self.shape == 'circle':
            cx, cy, radius, _ = self.coords
            return (cx - radius, cy - radius, cx + radius, cy + radius)
        
        elif self.shape == 'polygon':
            xs = [p[0] for p in self.coords]
            ys = [p[1] for p in self.coords]
            return (min(xs), min(ys), max(xs), max(ys))
        
        return (0, 0, 0, 0)
    
    def get_center(self) -> Tuple[float, float]:
        """Get center point"""
        if self.shape == 'rectangle':
            x1, y1, x2, y2 = self.coords
            return ((x1 + x2) / 2, (y1 + y2) / 2)
        
        elif self.shape == 'circle':
            cx, cy, _, _ = self.coords
            return (cx, cy)
        
        elif self.shape == 'polygon':
            xs = [p[0] for p in self.coords]
            ys = [p[1] for p in self.coords]
            return (sum(xs) / len(xs), sum(ys) / len(ys))
        
        return (0, 0)
    
    def get_area(self) -> float:
        """Calculate area"""
        if self.shape == 'rectangle':
            x1, y1, x2, y2 = self.coords
            return (x2 - x1) * (y2 - y1)
        
        elif self.shape == 'circle':
            _, _, radius, _ = self.coords
            return np.pi * radius ** 2
        
        elif self.shape == 'polygon':
            # Shoelace formula
            n = len(self.coords)
            area = 0
            for i in range(n):
                j = (i + 1) % n
                area += self.coords[i][0] * self.coords[j][1]
                area -= self.coords[j][0] * self.coords[i][1]
            return abs(area) / 2
        
        return 0


class HotspotMapper:
    """
    Manages collection of hotspots with spatial indexing
    """
    
    def __init__(self, image_width: int, image_height: int):
        """
        Initialize hotspot mapper
        
        Args:
            image_width: Base image width
            image_height: Base image height
        """
        self.image_width = image_width
        self.image_height = image_height
        self.hotspots: List[Hotspot] = []
        self.hotspot_index: Dict[str, Hotspot] = {}
        
        # Spatial grid for fast lookup
        self.grid_size = 50
        self.grid = self._create_spatial_grid()
    
    def _create_spatial_grid(self) -> Dict:
        """Create spatial grid for fast point queries"""
        return {}
    
    def add_hotspot(
        self,
        coords: Tuple,
        data: Dict,
        shape: str = 'rectangle',
        **kwargs
    ) -> str:
        """
        Add hotspot
        
        Returns:
            hotspot_id
        """
        hotspot_id = str(uuid.uuid4())
        
        hotspot = Hotspot(
            id=hotspot_id,
            coords=coords,
            shape=shape,
            data=data,
            layer_index=len(self.hotspots),
            **kwargs
        )
        
        self.hotspots.append(hotspot)
        self.hotspot_index[hotspot_id] = hotspot
        self._add_to_spatial_grid(hotspot)
        
        return hotspot_id
    
    def _add_to_spatial_grid(self, hotspot: Hotspot) -> None:
        """Add hotspot to spatial grid"""
        bbox = hotspot.get_bounding_box()
        x1, y1, x2, y2 = bbox
        
        # Calculate grid cells this hotspot overlaps
        grid_x1 = int(x1 / self.grid_size)
        grid_y1 = int(y1 / self.grid_size)
        grid_x2 = int(x2 / self.grid_size)
        grid_y2 = int(y2 / self.grid_size)
        
        for gx in range(grid_x1, grid_x2 + 1):
            for gy in range(grid_y1, grid_y2 + 1):
                cell_key = (gx, gy)
                if cell_key not in self.grid:
                    self.grid[cell_key] = []
                self.grid[cell_key].append(hotspot.id)
    
    def get_hotspot(self, hotspot_id: str) -> Optional[Hotspot]:
        """Get hotspot by ID"""
        return self.hotspot_index.get(hotspot_id)
    
    def remove_hotspot(self, hotspot_id: str) -> bool:
        """Remove hotspot"""
        if hotspot_id not in self.hotspot_index:
            return False
        
        hotspot = self.hotspot_index[hotspot_id]
        self.hotspots.remove(hotspot)
        del self.hotspot_index[hotspot_id]
        self._remove_from_spatial_grid(hotspot)
        
        return True
    
    def _remove_from_spatial_grid(self, hotspot: Hotspot) -> None:
        """Remove hotspot from spatial grid"""
        for cell_hotspots in self.grid.values():
            if hotspot.id in cell_hotspots:
                cell_hotspots.remove(hotspot.id)
    
    def find_hotspot_at_point(self, x: float, y: float) -> Optional[Hotspot]:
        """
        Find hotspot at given point (fast spatial query)
        
        Returns:
            Hotspot or None
        """
        # Get grid cell
        grid_x = int(x / self.grid_size)
        grid_y = int(y / self.grid_size)
        cell_key = (grid_x, grid_y)
        
        if cell_key not in self.grid:
            return None
        
        # Check hotspots in this cell
        for hotspot_id in self.grid[cell_key]:
            hotspot = self.hotspot_index[hotspot_id]
            if hotspot.contains_point(x, y):
                return hotspot
        
        return None
    
    def find_all_hotspots_at_point(self, x: float, y: float) -> List[Hotspot]:
        """
        Find all hotspots at given point (for overlapping hotspots)
        
        Returns:
            List of hotspots (empty if none)
        """
        grid_x = int(x / self.grid_size)
        grid_y = int(y / self.grid_size)
        cell_key = (grid_x, grid_y)
        
        if cell_key not in self.grid:
            return []
        
        matches = []
        for hotspot_id in self.grid[cell_key]:
            hotspot = self.hotspot_index[hotspot_id]
            if hotspot.contains_point(x, y):
                matches.append(hotspot)
        
        # Sort by priority (higher priority first)
        matches.sort(key=lambda h: h.priority, reverse=True)
        
        return matches
    
    def find_overlapping_hotspots(self, hotspot: Hotspot) -> List[Hotspot]:
        """
        Find all hotspots that overlap with given hotspot
        
        Returns:
            List of overlapping hotspots
        """
        overlapping = []
        
        for other in self.hotspots:
            if other.id != hotspot.id and hotspot.overlaps_with(other):
                overlapping.append(other)
        
        return overlapping
    
    def get_hotspots_in_region(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float
    ) -> List[Hotspot]:
        """
        Get all hotspots in rectangular region
        
        Returns:
            List of hotspots in region
        """
        region_hotspots = []
        
        for hotspot in self.hotspots:
            bbox = hotspot.get_bounding_box()
            hx1, hy1, hx2, hy2 = bbox
            
            # Check if bounding boxes overlap
            if not (hx2 < x1 or x2 < hx1 or hy2 < y1 or y2 < hy1):
                region_hotspots.append(hotspot)
        
        return region_hotspots
    
    def optimize_layout(self, method: str = 'priority') -> None:
        """
        Optimize hotspot layout to minimize overlaps
        
        Args:
            method: 'priority', 'size', 'position'
        """
        if method == 'priority':
            # Sort by priority
            self.hotspots.sort(key=lambda h: h.priority, reverse=True)
        
        elif method == 'size':
            # Sort by size (larger first)
            self.hotspots.sort(key=lambda h: h.get_area(), reverse=True)
        
        elif method == 'position':
            # Sort by position (top-left to bottom-right)
            self.hotspots.sort(key=lambda h: (h.coords[1], h.coords[0]))
        
        # Update layer indices
        for idx, hotspot in enumerate(self.hotspots):
            hotspot.layer_index = idx
    
    def validate_hotspots(self) -> Dict[str, Any]:
        """
        Validate all hotspots
        
        Returns:
            Validation results
        """
        errors = []
        warnings = []
        
        for i, hotspot in enumerate(self.hotspots):
            # Check if within image bounds
            bbox = hotspot.get_bounding_box()
            x1, y1, x2, y2 = bbox
            
            if x1 < 0 or y1 < 0 or x2 > self.image_width or y2 > self.image_height:
                warnings.append(
                    f"Hotspot {i+1} ({hotspot.id[:8]}) extends outside image bounds"
                )
            
            # Check for very small hotspots
            area = hotspot.get_area()
            if area < 100:  # 10x10 pixels
                warnings.append(
                    f"Hotspot {i+1} ({hotspot.id[:8]}) is very small ({area:.0f}px²)"
                )
            
            # Check for overlaps
            overlaps = self.find_overlapping_hotspots(hotspot)
            if len(overlaps) > 0:
                warnings.append(
                    f"Hotspot {i+1} ({hotspot.id[:8]}) overlaps with "
                    f"{len(overlaps)} other hotspot(s)"
                )
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_hotspots': len(self.hotspots),
            'average_size': np.mean([h.get_area() for h in self.hotspots]) if self.hotspots else 0
        }
    
    def export_map(self) -> List[Dict]:
        """
        Export hotspot map as list of dictionaries
        
        Returns:
            List of hotspot data
        """
        return [
            {
                'id': h.id,
                'coords': h.coords,
                'shape': h.shape,
                'visible': h.visible,
                'clickable': h.clickable,
                'lazy_load': h.lazy_load,
                'priority': h.priority,
                'layer_index': h.layer_index,
                'data': h.data
            }
            for h in self.hotspots
        ]
    
    def import_map(self, hotspot_data: List[Dict]) -> None:
        """
        Import hotspot map from list of dictionaries
        
        Args:
            hotspot_data: List of hotspot dictionaries
        """
        self.hotspots.clear()
        self.hotspot_index.clear()
        self.grid.clear()
        
        for data in hotspot_data:
            self.add_hotspot(
                coords=tuple(data['coords']),
                data=data.get('data', {}),
                shape=data.get('shape', 'rectangle'),
                visible=data.get('visible', True),
                clickable=data.get('clickable', True),
                lazy_load=data.get('lazy_load', False),
                priority=data.get('priority', 5)
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about hotspots
        
        Returns:
            Statistics dictionary
        """
        if not self.hotspots:
            return {
                'total_hotspots': 0,
                'total_area': 0,
                'coverage_percent': 0
            }
        
        total_area = sum(h.get_area() for h in self.hotspots)
        image_area = self.image_width * self.image_height
        
        shape_counts = {}
        for hotspot in self.hotspots:
            shape_counts[hotspot.shape] = shape_counts.get(hotspot.shape, 0) + 1
        
        return {
            'total_hotspots': len(self.hotspots),
            'total_area': total_area,
            'coverage_percent': (total_area / image_area) * 100 if image_area > 0 else 0,
            'average_area': total_area / len(self.hotspots),
            'shapes': shape_counts,
            'lazy_load_count': sum(1 for h in self.hotspots if h.lazy_load),
            'overlapping_count': len([h for h in self.hotspots if len(self.find_overlapping_hotspots(h)) > 0])
        }