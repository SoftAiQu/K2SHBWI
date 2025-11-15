"""
Desktop Viewer - Display K2SHBWI files using desktop GUI
"""

from pathlib import Path
from typing import Dict, Any
import io

try:
    import tkinter as tk
    from tkinter import messagebox
    from PIL import Image, ImageTk
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

from ..core.decoder import K2SHBWIDecoder


class DesktopViewer:
    """Display K2SHBWI files using desktop GUI (Tkinter)"""
    
    def __init__(self):
        """Initialize desktop viewer"""
        self.decoder = K2SHBWIDecoder()
        self.current_hotspot_index = 0
        
        if not HAS_TKINTER:
            raise ImportError("Tkinter is required for desktop viewer. Ensure Python is installed with Tkinter support.")
    
    def view(self, k2sh_file: str) -> Dict[str, Any]:
        """
        View K2SHBWI file in desktop GUI
        
        Args:
            k2sh_file: Path to K2SHBWI file
            
        Returns:
            Dictionary with viewer info
        """
        try:
            # Decode K2SHBWI file
            result = self.decoder.decode(k2sh_file)
            
            # Extract components
            if isinstance(result, tuple) and len(result) >= 4:
                header, metadata, hotspots, data = result[:4]
            else:
                header = getattr(result, 'header', {})
                metadata = getattr(result, 'metadata', {})
                hotspots = getattr(result, 'hotspots', [])
                data = getattr(result, 'image_data', {})
            
            # Extract image
            image_data = data if isinstance(data, bytes) else data.get('image_data', b'')
            if not image_data:
                return {'status': 'error', 'message': 'No image data found'}
            
            image = Image.open(io.BytesIO(image_data))
            
            # Create GUI window
            self._create_window(image, metadata, hotspots, k2sh_file)
            
            return {
                'status': 'success',
                'message': 'Desktop viewer window opened',
                'hotspots_count': len(hotspots) if hotspots else 0
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _create_window(self, image: Image.Image, metadata: Dict, hotspots: list, filename: str):
        """Create main GUI window"""
        
        # Create root window
        root = tk.Tk()
        root.title(metadata.get('title', 'K2SHBWI Viewer'))
        root.geometry('1000x700')
        
        # Create frame structure
        top_frame = tk.Frame(root, bg='#f0f0f0', height=60)
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            top_frame,
            text=metadata.get('title', 'K2SHBWI Presentation'),
            font=('Arial', 18, 'bold'),
            bg='#f0f0f0',
            fg='#667eea'
        )
        title_label.pack(pady=10)
        
        # Main content frame
        content_frame = tk.Frame(root)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Image label
        photo = ImageTk.PhotoImage(image.resize((600, 450), Image.Resampling.LANCZOS))
        image_label = tk.Label(content_frame, image=photo, bg='white')
        image_label.image = photo  # Keep a reference
        image_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Right panel for info
        right_frame = tk.Frame(content_frame, bg='#f9f9f9', width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        right_frame.pack_propagate(False)
        
        # File info
        info_label = tk.Label(
            right_frame,
            text='📋 File Information',
            font=('Arial', 12, 'bold'),
            bg='#f9f9f9',
            fg='#667eea'
        )
        info_label.pack(anchor=tk.W, pady=(10, 5))
        
        # File details
        details_text = tk.Text(right_frame, height=6, width=30, font=('Courier', 9))
        details_text.pack(fill=tk.X, padx=5)
        details_text.insert(tk.END, f"File: {Path(filename).name}\n")
        details_text.insert(tk.END, f"Title: {metadata.get('title', 'N/A')}\n")
        details_text.insert(tk.END, f"Image Size: {image.size[0]}x{image.size[1]}\n")
        details_text.insert(tk.END, f"Hotspots: {len(hotspots) if hotspots else 0}\n")
        details_text.config(state=tk.DISABLED)
        
        # Hotspots section
        if hotspots:
            hotspots_label = tk.Label(
                right_frame,
                text=f'🎯 Hotspots ({len(hotspots)})',
                font=('Arial', 11, 'bold'),
                bg='#f9f9f9',
                fg='#667eea'
            )
            hotspots_label.pack(anchor=tk.W, pady=(15, 5))
            
            # Hotspots list
            hotspots_text = tk.Text(right_frame, height=15, width=30, font=('Courier', 8))
            hotspots_text.pack(fill=tk.BOTH, expand=True, padx=5)
            
            for i, hotspot in enumerate(hotspots, 1):
                title_hs = hotspot.get('data', {}).get('user_data', {}).get('title', f'Hotspot {i}')
                description_hs = hotspot.get('data', {}).get('user_data', {}).get('description', '')
                hotspots_text.insert(tk.END, f"#{i} {title_hs}\n")
                if description_hs:
                    hotspots_text.insert(tk.END, f"   {description_hs}\n")
                hotspots_text.insert(tk.END, "\n")
            
            hotspots_text.config(state=tk.DISABLED)
        
        # Bottom button frame
        button_frame = tk.Frame(root, bg='#f0f0f0', height=50)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        button_frame.pack_propagate(False)
        
        close_button = tk.Button(
            button_frame,
            text='Close',
            command=root.quit,
            font=('Arial', 10),
            bg='#667eea',
            fg='white',
            padx=20,
            pady=8,
            relief=tk.FLAT
        )
        close_button.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Start GUI loop
        root.mainloop()
