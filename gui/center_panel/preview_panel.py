# gui/center_panel/preview_panel.py
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from canvas.video_item import VideoItem

class PreviewPanel(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(0, 0, 1080, 1920)
        
        # Mapping ID -> Visual Item agar update cepat tanpa loop scene
        self.visual_items = {} 

    # --- SLOTS (Reaksi terhadap Event) ---

    def on_layer_created(self, layer_data):
        """Dipanggil saat ada layer baru dibuat di controller"""
        item = VideoItem()
        # Kita asumsikan VideoItem punya method set_data atau kita set manual
        item.set_video_source(layer_data.path) # Contoh
        
        # Simpan ID di item agar bisa dilacak balik jika diklik di canvas
        item.setData(0, layer_data.id) 
        
        self.scene.addItem(item)
        self.visual_items[layer_data.id] = item

    def on_property_changed(self, layer_id, props):
        """Update visual realtime"""
        if layer_id in self.visual_items:
            item = self.visual_items[layer_id]
            
            # Update visual item sesuai properti yang berubah
            if "x" in props: item.setX(props["x"])
            if "y" in props: item.setY(props["y"])
            if "scale" in props: item.setScale(props["scale"] / 100.0)
            if "rotation" in props: item.setRotation(props["rotation"])
            
            item.update()

    def on_layer_removed(self, layer_id):
        if layer_id in self.visual_items:
            item = self.visual_items[layer_id]
            self.scene.removeItem(item)
            del self.visual_items[layer_id]

    def on_selection_changed(self, layer_data):
        # Deselect semua dulu
        for item in self.visual_items.values():
            item.setSelected(False)
            
        # Select target
        if layer_data and layer_data.id in self.visual_items:
            self.visual_items[layer_data.id].setSelected(True)