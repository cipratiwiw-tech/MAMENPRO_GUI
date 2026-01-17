from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QPainter

from canvas.video_item import VideoItem
from canvas.text_item import TextItem

class PreviewPanel(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 1. Setup Canvas (FHD Default)
        self.scene_width = 1920
        self.scene_height = 1080
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(0, 0, self.scene_width, self.scene_height)
        self.scene.setBackgroundBrush(QBrush(QColor("#000000"))) # Hitam Cinema
        
        # 2. Optimization Render
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # 3. UI Tweaks
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # 4. Registry
        self.visual_registry = {} # Map ID -> QGraphicsItem

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_canvas()

    def fit_canvas(self):
        self.fitInView(
            QRectF(0, 0, self.scene_width, self.scene_height), 
            Qt.KeepAspectRatio
        )

    # =========================================================
    # CORE VISUAL SYNC (JANTUNG VISUAL BARU)
    # =========================================================

    def sync_layer_visibility(self, active_ids: list):
        """
        [BARU] Menerima daftar ID yang HARUS muncul dari Controller.
        PreviewPanel bertindak sebagai bos yang menyuruh item Show/Hide.
        """
        active_set = set(active_ids) # Ubah ke Set agar pencarian cepat
        
        for layer_id, item in self.visual_registry.items():
            should_show = layer_id in active_set
            
            # Optimasi: Hanya setVisible jika status benar-benar berubah
            if item.isVisible() != should_show:
                item.setVisible(should_show)
                
                # Opsional: Reset state jika item baru muncul
                if should_show:
                    item.update() 

    def on_time_changed(self, t: float):
        """
        [BARU] Meneruskan waktu global ke setiap item yang SEDANG AKTIF.
        Hanya untuk keperluan animasi internal (misal: video frame seeking),
        BUKAN untuk menentukan visibility.
        """
        for item in self.visual_registry.values():
            if item.isVisible() and hasattr(item, 'sync_frame'):
                item.sync_frame(t)

    # =========================================================
    # CRUD VISUAL (STANDARD)
    # =========================================================
    
    def on_layer_created(self, layer_data):
        if layer_data.id in self.visual_registry: return
        
        item = None
        # Factory Sederhana
        if layer_data.type == 'text':
            item = TextItem(layer_data.id, layer_data.properties.get('text_content', 'Text'))
        elif layer_data.type in ['video', 'image']:
            item = VideoItem(layer_data.id, layer_data.path)
            
        if item:
            # Set properti awal
            item.update_properties(layer_data.properties, layer_data.z_index)
            self.scene.addItem(item)
            self.visual_registry[layer_data.id] = item
            
            # Default hide dulu, nanti Controller yang nyalakan via sync_layer_visibility
            item.setVisible(False) 
            
    def on_layer_removed(self, layer_id):
        if layer_id in self.visual_registry:
            item = self.visual_registry[layer_id]
            self.scene.removeItem(item)
            del self.visual_registry[layer_id]

    def clear_visual(self):
        self.scene.clear()
        self.visual_registry.clear()

    def on_property_changed(self, layer_id, props):
        if layer_id in self.visual_registry:
            item = self.visual_registry[layer_id]
            # Handle Z-Index khusus jika ada di props
            if "z_index" in props:
                item.setZValue(props["z_index"])
            item.update_properties(props)

    def on_selection_changed(self, layer_data):
        self.scene.clearSelection()
        if layer_data and layer_data.id in self.visual_registry:
            item = self.visual_registry[layer_data.id]
            item.setSelected(True)
            
    def on_layers_reordered(self, updates):
        for data in updates:
            if data['id'] in self.visual_registry:
                self.visual_registry[data['id']].setZValue(data['z_index'])
        self.scene.update()