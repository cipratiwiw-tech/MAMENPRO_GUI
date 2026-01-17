# gui/center_panel/preview_panel.py
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPainter

# Import item-item visual yang baru kita buat
from canvas.video_item import VideoItem
from canvas.text_item import TextItem

class PreviewPanel(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Setup Scene (Kanvas)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Ukuran Canvas (Misal 1080p Portrait)
        self.scene.setSceneRect(0, 0, 1080, 1920)
        self.scene.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        
        # Visual Helper
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Mapping ID -> Object Visual (Agar Binder bisa update item yg spesifik)
        self.visual_registry = {}

    # --- SLOTS: REAKSI TERHADAP BINDER (LOGIC -> VIEW) ---
    
    def on_layer_created(self, layer_data):
        """Membuat item visual sesuai tipe layer"""
        item = None
        
        # Factory Logic sederhana
        if layer_data.type == 'text':
            item = TextItem(layer_data.id, layer_data.properties.get('text_content', 'Text'))
        else:
            # Video / Image
            item = VideoItem(layer_data.id, layer_data.path)
            
        if item:
            # Set properti awal
            item.update_properties(layer_data.properties)
            
            # Add ke scene
            self.scene.addItem(item)
            self.visual_registry[layer_data.id] = item
            
            # Agar saat diklik, PreviewPanel bisa lapor ke Binder (Seleksi Visual)
            # (Logic klik ada di event handler scene/view atau item itu sendiri)

    def on_layer_removed(self, layer_id):
        if layer_id in self.visual_registry:
            item = self.visual_registry[layer_id]
            self.scene.removeItem(item)
            del self.visual_registry[layer_id]

    def on_property_changed(self, layer_id, props):
        if layer_id in self.visual_registry:
            # Delegasikan update ke masing-masing item
            self.visual_registry[layer_id].update_properties(props)
            self.scene.update()

    def on_selection_changed(self, layer_data):
        # Bersihkan seleksi lama
        self.scene.clearSelection()
        
        if layer_data and layer_data.id in self.visual_registry:
            item = self.visual_registry[layer_data.id]
            item.setSelected(True)