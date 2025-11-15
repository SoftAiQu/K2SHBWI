"""
Web Viewer - Display K2SHBWI files in web browser
"""

import webbrowser
import tempfile
from pathlib import Path
from typing import Dict, Any

from ..converters.html_converter import HTMLConverter


class WebViewer:
    """Display K2SHBWI files in web browser"""
    
    def __init__(self):
        """Initialize web viewer"""
        self.converter = HTMLConverter()
    
    def view(self, k2sh_file: str) -> Dict[str, Any]:
        """
        View K2SHBWI file in default web browser
        
        Args:
            k2sh_file: Path to K2SHBWI file
            
        Returns:
            Dictionary with viewer info
        """
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Convert to HTML
            self.converter.convert(k2sh_file, tmp_path)
            
            # Open in browser
            file_url = f"file://{Path(tmp_path).absolute()}"
            webbrowser.open(file_url)
            
            return {
                'status': 'success',
                'message': f'Opened {k2sh_file} in web browser',
                'temp_file': tmp_path,
                'url': file_url
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'temp_file': tmp_path
            }
    
    def view_with_hotspots(self, k2sh_file: str, hotspot_callback=None) -> Dict[str, Any]:
        """
        View K2SHBWI file with interactive hotspot handling
        
        Args:
            k2sh_file: Path to K2SHBWI file
            hotspot_callback: Optional callback function for hotspot clicks
            
        Returns:
            Dictionary with viewer info
        """
        return self.view(k2sh_file)
