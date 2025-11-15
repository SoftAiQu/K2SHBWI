"""
Data Layer Management and Optimization
"""

import json
import hashlib
from typing import Dict, List, Any, Optional
from collections import defaultdict
import copy


class DataLayer:
    """Represents a single data layer"""
    
    def __init__(self, data: Dict[str, Any], layer_id: Optional[str] = None):
        """
        Initialize data layer
        
        Args:
            data: Layer data (JSON-serializable)
            layer_id: Optional layer ID (auto-generated if not provided)
        """
        self.data = data
        self.layer_id = layer_id or self._generate_id()
        self.content_hash = self._compute_hash()
        self.size_bytes = len(json.dumps(data).encode())
        self.optimized = False
    
    def _generate_id(self) -> str:
        """Generate unique layer ID"""
        return hashlib.md5(
            json.dumps(self.data, sort_keys=True).encode()
        ).hexdigest()[:16]
    
    def _compute_hash(self) -> str:
        """Compute content hash"""
        return hashlib.blake2b(
            json.dumps(self.data, sort_keys=True).encode(),
            digest_size=16
        ).hexdigest()
    
    def get_keys(self, prefix: str = '', recursive: bool = True) -> set:
        """
        Get all keys in data layer
        
        Args:
            prefix: Key prefix
            recursive: Recursively get nested keys
            
        Returns:
            Set of keys
        """
        keys = set()
        
        def extract_keys(obj, current_prefix=''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    full_key = f"{current_prefix}.{key}" if current_prefix else key
                    keys.add(full_key)
                    if recursive and isinstance(value, (dict, list)):
                        extract_keys(value, full_key)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    if isinstance(item, (dict, list)):
                        extract_keys(item, f"{current_prefix}[{idx}]")
        
        extract_keys(self.data, prefix)
        return keys
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get value by key path (dot notation)
        
        Args:
            key_path: Dot-separated key path (e.g., "user.name")
            default: Default value if key not found
            
        Returns:
            Value or default
        """
        keys = key_path.split('.')
        value = self.data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def similarity_to(self, other: 'DataLayer') -> float:
        """
        Calculate similarity to another layer (0.0 to 1.0)
        
        Args:
            other: Another data layer
            
        Returns:
            Similarity score
        """
        # Get all keys from both layers
        keys1 = self.get_keys()
        keys2 = other.get_keys()
        
        # Jaccard similarity of keys
        intersection = len(keys1 & keys2)
        union = len(keys1 | keys2)
        
        if union == 0:
            return 0.0
        
        key_similarity = intersection / union
        
        # Content similarity (for shared keys)
        shared_keys = keys1 & keys2
        if not shared_keys:
            return key_similarity
        
        content_matches = 0
        for key in shared_keys:
            val1 = self.get_value(key)
            val2 = other.get_value(key)
            
            if val1 == val2:
                content_matches += 1
        
        content_similarity = content_matches / len(shared_keys)
        
        # Combined similarity (weighted average)
        return 0.4 * key_similarity + 0.6 * content_similarity


class DataLayerManager:
    """
    Manages multiple data layers with optimization
    """
    
    def __init__(self):
        """Initialize data layer manager"""
        self.layers: List[DataLayer] = []
        self.layer_index: Dict[str, DataLayer] = {}
        self.content_hash_index: Dict[str, List[str]] = defaultdict(list)
    
    def add_layer(self, data: Dict[str, Any], layer_id: Optional[str] = None) -> str:
        """
        Add data layer
        
        Args:
            data: Layer data
            layer_id: Optional layer ID
            
        Returns:
            layer_id
        """
        layer = DataLayer(data, layer_id)
        
        # Check for duplicate content
        if layer.content_hash in self.content_hash_index:
            # Return existing layer ID (deduplication)
            return self.content_hash_index[layer.content_hash][0]
        
        self.layers.append(layer)
        self.layer_index[layer.layer_id] = layer
        self.content_hash_index[layer.content_hash].append(layer.layer_id)
        
        return layer.layer_id
    
    def get_layer(self, layer_id: str) -> Optional[DataLayer]:
        """Get layer by ID"""
        return self.layer_index.get(layer_id)
    
    def remove_layer(self, layer_id: str) -> bool:
        """Remove layer"""
        if layer_id not in self.layer_index:
            return False
        
        layer = self.layer_index[layer_id]
        self.layers.remove(layer)
        del self.layer_index[layer_id]
        self.content_hash_index[layer.content_hash].remove(layer_id)
        
        return True
    
    def find_similar_layers(
        self,
        layer: DataLayer,
        min_similarity: float = 0.7
    ) -> List[tuple]:
        """
        Find similar layers
        
        Args:
            layer: Reference layer
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (layer_id, similarity_score) tuples
        """
        similar = []
        
        for other in self.layers:
            if other.layer_id != layer.layer_id:
                similarity = layer.similarity_to(other)
                if similarity >= min_similarity:
                    similar.append((other.layer_id, similarity))
        
        # Sort by similarity (descending)
        similar.sort(key=lambda x: x[1], reverse=True)
        
        return similar
    
    def group_similar_layers(
        self,
        min_similarity: float = 0.7
    ) -> List[List[str]]:
        """
        Group similar layers for optimization
        
        Args:
            min_similarity: Minimum similarity for grouping
            
        Returns:
            List of layer ID groups
        """
        groups = []
        processed = set()
        
        for layer in self.layers:
            if layer.layer_id in processed:
                continue
            
            # Find similar layers
            similar = self.find_similar_layers(layer, min_similarity)
            
            if similar:
                # Create group
                group = [layer.layer_id]
                for similar_id, _ in similar:
                    if similar_id not in processed:
                        group.append(similar_id)
                        processed.add(similar_id)
                
                groups.append(group)
                processed.add(layer.layer_id)
            else:
                # Single layer group
                groups.append([layer.layer_id])
                processed.add(layer.layer_id)
        
        return groups
    
    def compute_differential(
        self,
        base_layer_id: str,
        target_layer_id: str
    ) -> Dict[str, Any]:
        """
        Compute difference between two layers
        
        Args:
            base_layer_id: Base layer ID
            target_layer_id: Target layer ID
            
        Returns:
            Differential data (JSON patch format)
        """
        base = self.get_layer(base_layer_id)
        target = self.get_layer(target_layer_id)
        
        if not base or not target:
            return {}
        
        return self._compute_diff(base.data, target.data)
    
    def _compute_diff(self, base: Any, target: Any, path: str = '') -> Dict:
        """
        Recursively compute diff
        
        Returns:
            Dictionary of changes
        """
        changes = {
            'modified': {},
            'added': {},
            'removed': {}
        }
        
        if type(base) != type(target):
            changes['modified'][path] = target
            return changes
        
        if isinstance(base, dict):
            # Check for modifications and additions
            for key in target:
                current_path = f"{path}.{key}" if path else key
                
                if key not in base:
                    changes['added'][current_path] = target[key]
                elif base[key] != target[key]:
                    nested_changes = self._compute_diff(
                        base[key],
                        target[key],
                        current_path
                    )
                    changes['modified'].update(nested_changes['modified'])
                    changes['added'].update(nested_changes['added'])
                    changes['removed'].update(nested_changes['removed'])
            
            # Check for removals
            for key in base:
                if key not in target:
                    current_path = f"{path}.{key}" if path else key
                    changes['removed'][current_path] = base[key]
        
        elif isinstance(base, list):
            if base != target:
                changes['modified'][path] = target
        
        else:
            if base != target:
                changes['modified'][path] = target
        
        return changes
    
    def apply_differential(
        self,
        base_layer_id: str,
        diff: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply differential to base layer
        
        Args:
            base_layer_id: Base layer ID
            diff: Differential data
            
        Returns:
            Reconstructed data
        """
        base = self.get_layer(base_layer_id)
        if not base:
            return {}
        
        result = copy.deepcopy(base.data)
        
        # Apply modifications
        for path, value in diff.get('modified', {}).items():
            self._set_value(result, path, value)
        
        # Apply additions
        for path, value in diff.get('added', {}).items():
            self._set_value(result, path, value)
        
        # Apply removals
        for path in diff.get('removed', {}).keys():
            self._delete_value(result, path)
        
        return result
    
    def _set_value(self, data: Dict, path: str, value: Any) -> None:
        """Set value at path"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _delete_value(self, data: Dict, path: str) -> None:
        """Delete value at path"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                return
            current = current[key]
        
        if keys[-1] in current:
            del current[keys[-1]]
    
    def optimize_layers(self) -> Dict[str, Any]:
        """
        Optimize all layers (deduplication + differential compression)
        
        Returns:
            Optimization statistics
        """
        original_size = sum(layer.size_bytes for layer in self.layers)
        
        # Group similar layers
        groups = self.group_similar_layers(min_similarity=0.7)
        
        optimized_size = 0
        differential_groups = []
        
        for group in groups:
            if len(group) == 1:
                # Single layer, no optimization
                layer = self.get_layer(group[0])
                optimized_size += layer.size_bytes
            else:
                # Multiple similar layers - use differential compression
                base_id = group[0]
                base_layer = self.get_layer(base_id)
                optimized_size += base_layer.size_bytes
                
                diffs = []
                for target_id in group[1:]:
                    diff = self.compute_differential(base_id, target_id)
                    diff_size = len(json.dumps(diff).encode())
                    optimized_size += diff_size
                    diffs.append({
                        'target_id': target_id,
                        'diff': diff,
                        'size': diff_size
                    })
                
                differential_groups.append({
                    'base_id': base_id,
                    'diffs': diffs
                })
        
        return {
            'original_size': original_size,
            'optimized_size': optimized_size,
            'reduction_bytes': original_size - optimized_size,
            'reduction_percent': ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0,
            'total_layers': len(self.layers),
            'groups': len(groups),
            'differential_groups': len(differential_groups)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about data layers
        
        Returns:
            Statistics dictionary
        """
        if not self.layers:
            return {
                'total_layers': 0,
                'total_size': 0,
                'unique_content': 0
            }
        
        total_size = sum(layer.size_bytes for layer in self.layers)
        unique_content = len(self.content_hash_index)
        
        return {
            'total_layers': len(self.layers),
            'total_size': total_size,
            'average_size': total_size / len(self.layers),
            'unique_content': unique_content,
            'duplicate_count': len(self.layers) - unique_content,
            'deduplication_potential': (len(self.layers) - unique_content) / len(self.layers) * 100 if len(self.layers) > 0 else 0
        }