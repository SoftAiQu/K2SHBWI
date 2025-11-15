"""
K2SHBWI GUI Creator Application (PyQt6)
"""

import sys
from typing import Optional, List, Tuple
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem,
    QDockWidget, QListWidget, QListWidgetItem, QMessageBox, QProgressDialog,
    QTabWidget, QFormLayout, QComboBox, QSpinBox, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QThread
from PyQt6.QtGui import (
    QPixmap, QImage, QPen, QBrush, QColor, QPainter, QAction, QIcon
)
from PIL import Image
import json

from src.creator.builder import K2SHBWIBuilder
from src.creator.validator import K2SHBWIValidator


class BuilderThread(QThread):
    """Background thread for building K2SHBWI files"""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, builder: K2SHBWIBuilder, output_path: str):
        super().__init__()
        self.builder = builder
        self.output_path = output_path
    
    def run(self):
        try:
            self.progress.emit("Building K2SHBWI file...")
            stats = self.builder.build(self.output_path, verbose=False)
            self.finished.emit(stats)
        except Exception as e:
            self.error.emit(str(e))


class HotspotItem(QGraphicsRectItem):
    """Graphics item representing a hotspot"""
    
    def __init__(self, rect: QRectF, hotspot_id: str):
        super().__init__(rect)
        self.hotspot_id = hotspot_id
        
        # Style
        pen = QPen(QColor(255, 0, 0, 200))
        pen.setWidth(2)
        self.setPen(pen)
        
        brush = QBrush(QColor(255, 0, 0, 50))
        self.setBrush(brush)
        
        # Make interactive
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges)


class ImageCanvas(QGraphicsView):
    """Interactive canvas for editing hotspots"""
    
    hotspot_created = pyqtSignal(tuple)  # (x1, y1, x2, y2)
    hotspot_selected = pyqtSignal(str)   # hotspot_id
    
    def __init__(self):
        super().__init__()
        
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        self.image_item: Optional[QGraphicsPixmapItem] = None
        self.hotspot_items: dict = {}  # hotspot_id -> HotspotItem
        
        self.drawing = False
        self.start_point: Optional[QPointF] = None
        self.current_rect: Optional[QGraphicsRectItem] = None
        
        # Setup
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    def load_image(self, image_path: str):
        """Load image onto canvas"""
        pixmap = QPixmap(image_path)
        
        # Clear scene
        self.scene.clear()
        self.hotspot_items.clear()
        
        # Add image
        self.image_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.image_item)
        
        # Fit in view
        self.fitInView(self.image_item, Qt.AspectRatioMode.KeepAspectRatio)
    
    def add_hotspot(self, hotspot_id: str, coords: Tuple[float, float, float, float]):
        """Add hotspot to canvas"""
        x1, y1, x2, y2 = coords
        rect = QRectF(x1, y1, x2 - x1, y2 - y1)
        
        item = HotspotItem(rect, hotspot_id)
        self.scene.addItem(item)
        self.hotspot_items[hotspot_id] = item
    
    def remove_hotspot(self, hotspot_id: str):
        """Remove hotspot from canvas"""
        if hotspot_id in self.hotspot_items:
            item = self.hotspot_items[hotspot_id]
            self.scene.removeItem(item)
            del self.hotspot_items[hotspot_id]
    
    def mousePressEvent(self, event):
        """Start drawing hotspot"""
        if event.button() == Qt.MouseButton.LeftButton and self.image_item:
            pos = self.mapToScene(event.pos())
            
            # Check if clicked on existing hotspot
            item = self.scene.itemAt(pos, self.transform())
            if isinstance(item, HotspotItem):
                self.hotspot_selected.emit(item.hotspot_id)
                super().mousePressEvent(event)
                return
            
            # Start drawing new hotspot
            self.drawing = True
            self.start_point = pos
            
            # Create temporary rectangle
            self.current_rect = QGraphicsRectItem(QRectF(pos, pos))
            pen = QPen(QColor(0, 255, 0, 200))
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.DashLine)
            self.current_rect.setPen(pen)
            self.scene.addItem(self.current_rect)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Update hotspot while drawing"""
        if self.drawing and self.current_rect:
            pos = self.mapToScene(event.pos())
            rect = QRectF(self.start_point, pos).normalized()
            self.current_rect.setRect(rect)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Finish drawing hotspot"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            
            if self.current_rect:
                rect = self.current_rect.rect()
                
                # Remove temporary rectangle
                self.scene.removeItem(self.current_rect)
                self.current_rect = None
                
                # Emit coords if valid size
                if rect.width() > 10 and rect.height() > 10:
                    coords = (
                        rect.x(),
                        rect.y(),
                        rect.x() + rect.width(),
                        rect.y() + rect.height()
                    )
                    self.hotspot_created.emit(coords)
        
        super().mouseReleaseEvent(event)


class K2SHBWICreatorGUI(QMainWindow):
    """Main GUI application for creating K2SHBWI files"""
    
    def __init__(self):
        super().__init__()
        
        self.builder = K2SHBWIBuilder()
        self.current_image_path: Optional[str] = None
        self.current_hotspot_id: Optional[str] = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("K2SHBWI Creator")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Canvas (center)
        self.canvas = ImageCanvas()
        self.canvas.hotspot_created.connect(self.on_hotspot_created)
        self.canvas.hotspot_selected.connect(self.on_hotspot_selected)
        main_layout.addWidget(self.canvas, stretch=3)
        
        # Right panel
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, stretch=1)
        
        # Menu bar
        self.create_menu_bar()
        
        # Toolbar
        self.create_toolbar()
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Image...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        build_action = QAction("&Build K2SHBWI...", self)
        build_action.setShortcut("Ctrl+B")
        build_action.triggered.connect(self.build_file)
        file_menu.addAction(build_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        delete_action = QAction("&Delete Hotspot", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_current_hotspot)
        edit_menu.addAction(delete_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        auto_detect_action = QAction("&Auto-Detect Hotspots", self)
        auto_detect_action.triggered.connect(self.auto_detect_hotspots)
        tools_menu.addAction(auto_detect_action)
        
        validate_action = QAction("&Validate", self)
        validate_action.triggered.connect(self.validate_content)
        tools_menu.addAction(validate_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create toolbar"""
        toolbar = self.addToolBar("Main")
        
        # Open image
        open_btn = QPushButton("Open Image")
        open_btn.clicked.connect(self.open_image)
        toolbar.addWidget(open_btn)
        
        toolbar.addSeparator()
        
        # Auto-detect
        auto_btn = QPushButton("Auto-Detect Hotspots")
        auto_btn.clicked.connect(self.auto_detect_hotspots)
        toolbar.addWidget(auto_btn)
        
        toolbar.addSeparator()
        
        # Build
        build_btn = QPushButton("Build K2SHBWI")
        build_btn.clicked.connect(self.build_file)
        toolbar.addWidget(build_btn)
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with tabs"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Metadata tab
        metadata_tab = self.create_metadata_tab()
        tabs.addTab(metadata_tab, "Metadata")
        
        # Hotspots tab
        hotspots_tab = self.create_hotspots_tab()
        tabs.addTab(hotspots_tab, "Hotspots")
        
        # Settings tab
        settings_tab = self.create_settings_tab()
        tabs.addTab(settings_tab, "Settings")
        
        layout.addWidget(tabs)
        
        return panel
    
    def create_metadata_tab(self) -> QWidget:
        """Create metadata editing tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter title...")
        layout.addRow("Title:", self.title_input)
        
        # Author
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Enter author...")
        layout.addRow("Author:", self.author_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter description...")
        self.description_input.setMaximumHeight(100)
        layout.addRow("Description:", self.description_input)
        
        # Tags
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("tag1, tag2, tag3")
        layout.addRow("Tags:", self.tags_input)
        
        layout.addStretch()
        
        return widget
    
    def create_hotspots_tab(self) -> QWidget:
        """Create hotspots list and editor tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Hotspot list
        label = QLabel("Hotspots:")
        layout.addWidget(label)
        
        self.hotspot_list = QListWidget()
        self.hotspot_list.itemClicked.connect(self.on_hotspot_list_clicked)
        layout.addWidget(self.hotspot_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_hotspot_manual)
        btn_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_current_hotspot)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        # Hotspot data editor
        editor_group = QGroupBox("Hotspot Data")
        editor_layout = QVBoxLayout(editor_group)
        
        self.hotspot_data_input = QTextEdit()
        self.hotspot_data_input.setPlaceholderText('{\n  "title": "...",\n  "description": "..."\n}')
        editor_layout.addWidget(self.hotspot_data_input)
        
        save_data_btn = QPushButton("Save Data")
        save_data_btn.clicked.connect(self.save_hotspot_data)
        editor_layout.addWidget(save_data_btn)
        
        layout.addWidget(editor_group)
        
        return widget
    
    def create_settings_tab(self) -> QWidget:
        """Create settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Image quality
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(['low', 'medium', 'high', 'ultra'])
        self.quality_combo.setCurrentText('high')
        layout.addRow("Image Quality:", self.quality_combo)
        
        # Data algorithm
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(['adaptive', 'brotli', 'lzma', 'zstd'])
        self.algorithm_combo.setCurrentText('adaptive')
        layout.addRow("Data Algorithm:", self.algorithm_combo)
        
        # Deduplication
        self.dedup_check = QCheckBox("Enable Deduplication")
        self.dedup_check.setChecked(True)
        layout.addRow("", self.dedup_check)
        
        # Differential compression
        self.diff_check = QCheckBox("Enable Differential Compression")
        self.diff_check.setChecked(True)
        layout.addRow("", self.diff_check)
        
        layout.addStretch()
        
        return widget
    
    def open_image(self):
        """Open image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            try:
                # Load image
                self.canvas.load_image(file_path)
                self.current_image_path = file_path
                
                # Set in builder
                self.builder.set_base_image(file_path)
                
                self.statusBar().showMessage(f"Loaded: {file_path}")
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image:\n{str(e)}")
    
    def on_hotspot_created(self, coords: Tuple[float, float, float, float]):
        """Handle hotspot creation from canvas"""
        # Create dialog for hotspot data
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Add Hotspot")
        dialog.setText("Enter hotspot data (JSON format):")
        
        # For now, add with placeholder data
        data = {
            "title": "New Hotspot",
            "description": "Click to edit data"
        }
        
        try:
            hotspot_id = self.builder.add_hotspot(coords=coords, data=data)
            
            # Add to canvas
            self.canvas.add_hotspot(hotspot_id, coords)
            
            # Add to list
            self.add_hotspot_to_list(hotspot_id, coords, data)
            
            self.statusBar().showMessage(f"Hotspot added: {hotspot_id[:8]}...")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add hotspot:\n{str(e)}")
    
    def on_hotspot_selected(self, hotspot_id: str):
        """Handle hotspot selection"""
        self.current_hotspot_id = hotspot_id
        
        # Find in list and select
        for i in range(self.hotspot_list.count()):
            item = self.hotspot_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == hotspot_id:
                self.hotspot_list.setCurrentItem(item)
                break
        
        # Load data into editor
        hotspot = next((h for h in self.builder.hotspots if h['id'] == hotspot_id), None)
        if hotspot:
            data_json = json.dumps(hotspot['data'], indent=2)
            self.hotspot_data_input.setText(data_json)
    
    def on_hotspot_list_clicked(self, item: QListWidgetItem):
        """Handle hotspot list item click"""
        hotspot_id = item.data(Qt.ItemDataRole.UserRole)
        self.on_hotspot_selected(hotspot_id)
    
    def add_hotspot_to_list(self, hotspot_id: str, coords: Tuple, data: dict):
        """Add hotspot to list widget"""
        title = data.get('title', 'Untitled')
        x1, y1, x2, y2 = coords
        
        item_text = f"{title} ({int(x1)}, {int(y1)}, {int(x2)}, {int(y2)})"
        
        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, hotspot_id)
        self.hotspot_list.addItem(item)
    
    def add_hotspot_manual(self):
        """Add hotspot manually (no drawing)"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "Please open an image first")
            return
        
        # Use center of image as default
        if self.canvas.image_item:
            rect = self.canvas.image_item.boundingRect()
            center_x = rect.width() / 2
            center_y = rect.height() / 2
            
            coords = (
                center_x - 50,
                center_y - 50,
                center_x + 50,
                center_y + 50
            )
            
            self.on_hotspot_created(coords)
    
    def delete_current_hotspot(self):
        """Delete currently selected hotspot"""
        if not self.current_hotspot_id:
            QMessageBox.warning(self, "Warning", "No hotspot selected")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete selected hotspot?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from builder
            self.builder.remove_hotspot(self.current_hotspot_id)
            
            # Remove from canvas
            self.canvas.remove_hotspot(self.current_hotspot_id)
            
            # Remove from list
            for i in range(self.hotspot_list.count()):
                item = self.hotspot_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == self.current_hotspot_id:
                    self.hotspot_list.takeItem(i)
                    break
            
            self.current_hotspot_id = None
            self.hotspot_data_input.clear()
            
            self.statusBar().showMessage("Hotspot deleted")
    
    def save_hotspot_data(self):
        """Save edited hotspot data"""
        if not self.current_hotspot_id:
            QMessageBox.warning(self, "Warning", "No hotspot selected")
            return
        
        try:
            # Parse JSON
            data_text = self.hotspot_data_input.toPlainText()
            data = json.loads(data_text)
            
            # Update builder
            self.builder.update_hotspot(self.current_hotspot_id, data=data)
            
            # Update list item text
            for i in range(self.hotspot_list.count()):
                item = self.hotspot_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == self.current_hotspot_id:
                    title = data.get('title', 'Untitled')
                    hotspot = next((h for h in self.builder.hotspots if h['id'] == self.current_hotspot_id), None)
                    if hotspot:
                        x1, y1, x2, y2 = hotspot['coords']
                        item.setText(f"{title} ({int(x1)}, {int(y1)}, {int(x2)}, {int(y2)})")
                    break
            
            self.statusBar().showMessage("Hotspot data saved")
        
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error", f"Invalid JSON:\n{str(e)}")
    
    def auto_detect_hotspots(self):
        """Auto-detect hotspots using AI"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "Please open an image first")
            return
        
        try:
            # Show progress dialog
            progress = QProgressDialog("Detecting hotspots...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            
            # Detect hotspots
            suggestions = self.builder.auto_detect_hotspots()
            
            progress.close()
            
            if not suggestions:
                QMessageBox.information(self, "Info", "No hotspots detected")
                return
            
            # Ask user to confirm
            reply = QMessageBox.question(
                self,
                "Confirm",
                f"Found {len(suggestions)} potential hotspots. Add them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Apply suggestions
                ids = self.builder.apply_suggested_hotspots(suggestions)
                
                # Add to canvas and list
                for hotspot_id in ids:
                    hotspot = next((h for h in self.builder.hotspots if h['id'] == hotspot_id), None)
                    if hotspot:
                        self.canvas.add_hotspot(hotspot_id, hotspot['coords'])
                        self.add_hotspot_to_list(hotspot_id, hotspot['coords'], hotspot['data'])
                
                self.statusBar().showMessage(f"Added {len(ids)} hotspots")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Auto-detection failed:\n{str(e)}")
    
    def validate_content(self):
        """Validate current content"""
        try:
            validator = K2SHBWIValidator()
            
            # Validate
            is_valid = validator.validate_all(
                image=self.builder.base_image,
                hotspots=self.builder.hotspots,
                metadata=self.get_current_metadata(),
                config=self.get_current_config()
            )
            
            # Show report
            report = validator.get_report()
            
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Validation Report")
            dialog.setText(report)
            
            if is_valid:
                dialog.setIcon(QMessageBox.Icon.Information)
            else:
                dialog.setIcon(QMessageBox.Icon.Warning)
            
            dialog.exec()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Validation failed:\n{str(e)}")
    
    def build_file(self):
        """Build K2SHBWI file"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "Please open an image first")
            return
        
        # Get output path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save K2SHBWI File",
            "",
            "K2SHBWI Files (*.k2sh)"
        )
        
        if not file_path:
            return
        
        try:
            # Set metadata
            metadata = self.get_current_metadata()
            if metadata:
                self.builder.set_metadata(metadata)
            
            # Configure compression
            self.builder.configure_compression(
                image_quality=self.quality_combo.currentText(),
                data_algorithm=self.algorithm_combo.currentText(),
                enable_deduplication=self.dedup_check.isChecked(),
                enable_differential=self.diff_check.isChecked()
            )
            
            # Build in background thread
            progress = QProgressDialog("Building K2SHBWI file...", None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            
            self.build_thread = BuilderThread(self.builder, file_path)
            self.build_thread.finished.connect(lambda stats: self.on_build_finished(stats, progress))
            self.build_thread.error.connect(lambda msg: self.on_build_error(msg, progress))
            self.build_thread.start()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Build failed:\n{str(e)}")
    
    def on_build_finished(self, stats: dict, progress: QProgressDialog):
        """Handle build completion"""
        progress.close()
        
        QMessageBox.information(
            self,
            "Success",
            f"K2SHBWI file created successfully!\n\n"
            f"Size: {stats['output_size_mb']:.2f} MB\n"
            f"Compression: {stats['compression_ratio_percent']:.1f}%\n"
            f"Hotspots: {stats['hotspots_count']}"
        )
        
        self.statusBar().showMessage("Build complete")
    
    def on_build_error(self, error_msg: str, progress: QProgressDialog):
        """Handle build error"""
        progress.close()
        QMessageBox.critical(self, "Error", f"Build failed:\n{error_msg}")
    
    def get_current_metadata(self) -> dict:
        """Get metadata from form"""
        metadata = {}
        
        title = self.title_input.text().strip()
        if title:
            metadata['title'] = title
        
        author = self.author_input.text().strip()
        if author:
            metadata['author'] = author
        
        description = self.description_input.toPlainText().strip()
        if description:
            metadata['description'] = description
        
        tags = self.tags_input.text().strip()
        if tags:
            metadata['tags'] = [t.strip() for t in tags.split(',')]
        
        return metadata
    
    def get_current_config(self) -> dict:
        """Get configuration from form"""
        return {
            'compression': {
                'image_quality': self.quality_combo.currentText(),
                'data_algorithm': self.algorithm_combo.currentText(),
                'enable_deduplication': self.dedup_check.isChecked(),
                'enable_differential': self.diff_check.isChecked()
            }
        }
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About K2SHBWI Creator",
            "K2SHBWI Creator v1.0\n\n"
            "Create interactive image files with embedded data.\n\n"
            "© 2025 K2SHBWI Project"
        )


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("K2SHBWI Creator")
    
    window = K2SHBWICreatorGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()