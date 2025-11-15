"""
HTML Converter - Convert K2SHBWI files to interactive HTML
"""

import base64
import io
import json
from pathlib import Path
from typing import Dict
from PIL import Image
from bs4 import BeautifulSoup

from .base_converter import BaseConverter


class HTMLConverter(BaseConverter):
    """Convert K2SHBWI to interactive HTML with hotspots"""
    
    @property
    def format_name(self) -> str:
        return 'HTML'
    
    def _convert_impl(self, image: Image.Image, metadata: Dict, hotspots: list, output_path: str):
        """Convert to HTML with interactive hotspots"""
        
        # Encode image to base64
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # Create HTML structure
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata.get('title', 'K2SHBWI Presentation')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            width: 100%;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .image-container {{
            position: relative;
            display: inline-block;
            margin-bottom: 30px;
            width: 100%;
        }}
        
        .image-container img {{
            width: 100%;
            max-width: 900px;
            height: auto;
            display: block;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }}
        
        .hotspot {{
            position: absolute;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .hotspot-dot {{
            width: 16px;
            height: 16px;
            background: rgba(102, 126, 234, 0.8);
            border: 3px solid white;
            border-radius: 50%;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }}
        
        .hotspot:hover .hotspot-dot {{
            width: 24px;
            height: 24px;
            background: rgba(102, 126, 234, 1);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.5);
        }}
        
        .hotspot-tooltip {{
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 10px 15px;
            border-radius: 6px;
            font-size: 0.9em;
            white-space: nowrap;
            margin-bottom: 10px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            z-index: 10;
        }}
        
        .hotspot-tooltip::after {{
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: #333;
        }}
        
        .hotspot:hover .hotspot-tooltip {{
            opacity: 1;
        }}
        
        .metadata {{
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        
        .metadata h3 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 1.2em;
        }}
        
        .metadata p {{
            color: #666;
            margin: 5px 0;
            line-height: 1.6;
        }}
        
        .hotspots-legend {{
            background: #f9f9f9;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-top: 30px;
            border-radius: 4px;
        }}
        
        .hotspots-legend h3 {{
            color: #333;
            margin-bottom: 15px;
        }}
        
        .hotspot-item {{
            background: white;
            padding: 12px;
            margin: 8px 0;
            border-radius: 4px;
            border-left: 3px solid #667eea;
        }}
        
        .hotspot-item strong {{
            color: #667eea;
        }}
        
        .footer {{
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #ddd;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{metadata.get('title', 'Interactive Presentation')}</h1>
            <p>{metadata.get('description', '')}</p>
        </div>
        
        <div class="content">
            <div class="image-container" id="imageContainer">
                <img src="data:image/png;base64,{img_base64}" alt="Main image" id="mainImage">
"""
        
        # Add hotspots
        if hotspots:
            html_content += self._generate_hotspots_html(hotspots)
        
        # Add metadata section
        html_content += self._generate_metadata_html(metadata)
        
        # Add hotspots legend
        if hotspots:
            html_content += self._generate_legend_html(hotspots)
        
        # Close HTML
        html_content += """
            </div>
        </div>
        
        <div class="footer">
            <p>Generated from K2SHBWI format | Interactive Hotspot Presentation</p>
        </div>
    </div>
    
    <script>
        // Hotspot interaction
        document.querySelectorAll('.hotspot').forEach(hotspot => {{
            hotspot.addEventListener('click', function() {{
                alert(this.dataset.title + '\\n\\n' + this.dataset.description);
            }});
        }});
    </script>
</body>
</html>"""
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_hotspots_html(self, hotspots: list) -> str:
        """Generate HTML for hotspots overlays"""
        html = ""
        
        if not hotspots:
            return html
        
        # Get image dimensions from the first hotspot data
        for hotspot in hotspots:
            coords = hotspot.get('coords', (0, 0, 100, 100))
            title = hotspot.get('data', {}).get('user_data', {}).get('title', 'Hotspot')
            description = hotspot.get('data', {}).get('user_data', {}).get('description', '')
            
            x1, y1, x2, y2 = coords
            
            # Calculate position in percentages
            left = (x1 / 1000) * 100  # Assume 1000x1000 max for % calculation
            top = (y1 / 1000) * 100
            
            html += f"""
                <div class="hotspot" style="left: {left}%; top: {top}%;" 
                     data-title="{title}" data-description="{description}">
                    <div class="hotspot-dot"></div>
                    <div class="hotspot-tooltip">{title}</div>
                </div>
"""
        
        return html
    
    def _generate_metadata_html(self, metadata: Dict) -> str:
        """Generate HTML for metadata section"""
        if not metadata:
            return ""
        
        html = """
            <div class="metadata">
                <h3>📋 Information</h3>
"""
        
        for key, value in metadata.items():
            if key not in ['title', 'description']:
                html += f"""                <p><strong>{key}:</strong> {value}</p>
"""
        
        html += """            </div>
"""
        
        return html
    
    def _generate_legend_html(self, hotspots: list) -> str:
        """Generate HTML for hotspots legend"""
        if not hotspots:
            return ""
        
        html = """
            <div class="hotspots-legend">
                <h3>🎯 Interactive Hotspots ({} total)</h3>
""".format(len(hotspots))
        
        for i, hotspot in enumerate(hotspots, 1):
            title = hotspot.get('data', {}).get('user_data', {}).get('title', f'Hotspot {i}')
            description = hotspot.get('data', {}).get('user_data', {}).get('description', '')
            
            html += f"""                <div class="hotspot-item">
                    <strong>#{i} {title}</strong>
                    {f'<br><small>{description}</small>' if description else ''}
                </div>
"""
        
        html += """            </div>
"""
        
        return html
