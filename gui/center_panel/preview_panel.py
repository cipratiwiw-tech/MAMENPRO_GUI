# gui/center_panel/preview_panel.py
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QPainter

from canvas.video_item import VideoItem
from canvas.text_item import TextItem

class PreviewPanel(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        # [FIX] 1. DEFINISIKAN UKURAN DULU (PENTING! Agar tidak error saat resize)
        self.scene_width = 1080
        self.scene_height = 1920
        
        # 2. Setup Scene (Kanvas)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Gunakan variabel ukuran yang sudah dibuat di atas
        self.scene.setSceneRect(0, 0, self.scene_width, self.scene_height)
        self.scene.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        
        # Visual Helper
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # [BARU] Hilangkan Scrollbar agar bersih
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Mapping ID -> Object Visual
        self.visual_registry = {}

    # [BARU] Auto Fit Logic: Agar canvas 1080x1920 selalu muat di kotak kecil
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_canvas()

    def fit_canvas(self):
        # Pastikan variabel sudah ada sebelum dipakai (Safety Check)
        if hasattr(self, 'scene_width') and hasattr(self, 'scene_height'):
            # Fit seluruh scene_rect ke dalam view, menjaga aspek rasio
            self.fitInView(
                QRectF(0, 0, self.scene_width, self.scene_height), 
                Qt.KeepAspectRatio
            )
    
    # --- SLOTS: REAKSI TERHADAP BINDER (LOGIC -> VIEW) ---
    
    def on_layer_created(self, layer_data):
        item = None
        
        # 1. Filter Visual Only
        # Audio tidak perlu digambar di canvas preview visual
        if layer_data.type == 'audio':
            return 

        # 2. Factory Logic Sederhana
        if layer_data.type == 'text':
            item = TextItem(layer_data.id, layer_data.properties.get('text_content', 'Text'))
        else:
            # Video / Image
            item = VideoItem(layer_data.id, layer_data.path)
            
        if item:
            item.update_properties(layer_data.properties, layer_data.z_index)
            self.scene.addItem(item)
            self.visual_registry[layer_data.id] = item

    def on_layer_removed(self, layer_id):
        if layer_id in self.visual_registry:
            item = self.visual_registry[layer_id]
            self.scene.removeItem(item)
            del self.visual_registry[layer_id]

    def on_property_changed(self, layer_id, props):
        if layer_id in self.visual_registry:
            # Karena props adalah partial dict, kita tidak selalu punya z_index.
            # Idealnya Binder mengirim full object atau Z-index terpisah.
            # TAPI untuk simplifikasi, kita update properti visual saja.
            # Jika Z-index berubah (via Reorder), kita butuh method khusus 'on_layer_reordered'.
            
            # Untuk sekarang, kita panggil update_properties tanpa mengubah z_index default (0)
            # KECUALI jika props mengandung 'z_index' (dari controller)
            
            item = self.visual_registry[layer_id]
            current_z = item.zValue()
            new_z = props.get("z_index", current_z) # Pakai yg baru jika ada
            
            item.update_properties(props, new_z)
            self.scene.update()

    def on_selection_changed(self, layer_data):
        # Bersihkan seleksi lama
        self.scene.clearSelection()
        
        if layer_data and layer_data.id in self.visual_registry:
            item = self.visual_registry[layer_data.id]
            item.setSelected(True)
            
    # [BARU] Handler Spesifik Z-Index
    def on_layers_reordered(self, updates: list):
        """
        Menerima list dict: [{'id': '...', 'z_index': 0}, ...]
        Hanya update tumpukan visual. Hemat resource.
        """
        for data in updates:
            layer_id = data['id']
            new_z = data['z_index']
            
            if layer_id in self.visual_registry:
                item = self.visual_registry[layer_id]
                item.setZValue(new_z)
                
        # Trigger refresh scene
        self.scene.update()
        print("[PREVIEW] Z-Indexes updated.")
        
    # [BARU] API Resmi untuk Binder
    def clear_visual(self):
        """Membersihkan seluruh scene dan registry visual."""
        self.scene.clear()
        self.visual_registry.clear()
        print("[PREVIEW] Visual cleared.")
        
        # [BARU] Method yang dipanggil saat timer berjalan (Timeline Tick)
    def on_time_changed(self, t):
        # Broadcast waktu ke semua item visual
        for item in self.visual_registry.values():
            if hasattr(item, 'update_time'):
                item.update_time(t)
        
        # Opsional: Paksa redraw scene jika ada artefak visual
        # self.scene.update()