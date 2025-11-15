"""
PDF Converter - Convert K2SHBWI files to PDF with hotspots
"""

import io
import json
from pathlib import Path
from typing import Dict
from PIL import Image

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

from .base_converter import BaseConverter


class PDFConverter(BaseConverter):
    """Convert K2SHBWI to PDF with hotspot annotations"""
    
    @property
    def format_name(self) -> str:
        return 'PDF'
    
    def _convert_impl(self, image: Image.Image, metadata: Dict, hotspots: list, output_path: str):
        """Convert to PDF format"""
        
        if not HAS_REPORTLAB:
            # Fallback: Simple PDF using PIL with basic formatting
            self._create_simple_pdf(image, metadata, hotspots, output_path)
        else:
            # Full PDF with rich formatting
            self._create_advanced_pdf(image, metadata, hotspots, output_path)
    
    def _create_simple_pdf(self, image: Image.Image, metadata: Dict, hotspots: list, output_path: str):
        """Create simple PDF using PIL (fallback if reportlab not available)"""
        try:
            from PIL import ImageDraw, ImageFont
            import struct
            
            # Create a new image for PDF
            width, height = image.size
            # Add space for title and info
            pdf_height = height + 200
            pdf_image = Image.new('RGB', (width, pdf_height), color='white')
            
            # Paste original image
            pdf_image.paste(image, (0, 150))
            
            # Draw title
            draw = ImageDraw.Draw(pdf_image)
            title = metadata.get('title', 'K2SHBWI Presentation')
            try:
                font = ImageFont.truetype("arial.ttf", 24)
                font_small = ImageFont.truetype("arial.ttf", 12)
            except:
                font = ImageFont.load_default()
                font_small = font
            
            # Draw text
            draw.text((20, 20), title, fill='black', font=font)
            draw.text((20, 60), f"Hotspots: {len(hotspots)}", fill='gray', font=font_small)
            
            # Save as PDF via image
            pdf_image.convert('RGB').save(output_path, 'PDF')
            
        except Exception as e:
            # Final fallback: just save image
            image.save(output_path, 'PDF')
    
    def _create_advanced_pdf(self, image: Image.Image, metadata: Dict, hotspots: list, output_path: str):
        """Create advanced PDF with formatting using ReportLab"""
        
        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=12,
            alignment=1  # Center
        )
        
        # Add title
        title = metadata.get('title', 'K2SHBWI Presentation')
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add description
        description = metadata.get('description', '')
        if description:
            elements.append(Paragraph(description, styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
        
        # Add image
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_path = '/tmp/k2sh_temp_img.png'
        with open(img_path, 'wb') as f:
            f.write(img_buffer.getvalue())
        
        # Add image to PDF
        try:
            rl_image = RLImage(img_path, width=5*inch, height=3.75*inch)
            elements.append(rl_image)
        except:
            pass
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Add hotspots information
        if hotspots:
            elements.append(Paragraph(f"Interactive Hotspots ({len(hotspots)} total)", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            hotspot_data = []
            for i, hotspot in enumerate(hotspots, 1):
                title_hs = hotspot.get('data', {}).get('user_data', {}).get('title', f'Hotspot {i}')
                description_hs = hotspot.get('data', {}).get('user_data', {}).get('description', '')
                hotspot_data.append([str(i), title_hs, description_hs or '-'])
            
            if hotspot_data:
                hotspot_table = Table(hotspot_data, colWidths=[0.5*inch, 2*inch, 2.5*inch])
                hotspot_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
                ]))
                elements.append(hotspot_table)
        
        # Add metadata
        if metadata:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("File Information", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            meta_data = []
            for key, value in metadata.items():
                if key not in ['title', 'description']:
                    meta_data.append([str(key).capitalize(), str(value)])
            
            if meta_data:
                meta_table = Table(meta_data, colWidths=[2*inch, 3.5*inch])
                meta_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ]))
                elements.append(meta_table)
        
        # Build PDF
        try:
            doc.build(elements)
        except Exception as e:
            # Fallback to simple PDF
            self._create_simple_pdf(image, metadata, hotspots, output_path)
