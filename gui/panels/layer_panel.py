from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QBrush, QColor, QPen, QFont

# Konfigurasi Visual Timeline
ZOOM_LEVEL = 50.0  # 1 detik = 50 pixel
TRACK_HEIGHT = 40
HEADER_HEIGHT = 30

class TimelineClipItem(QGraphicsRectItem):
    """Representasi Visual dari Layer (Balok Warna)"""
    def __init__(self, layer_data, row_index):
        super().__init__()
        self.layer_id = layer_data.id
        self.setFlags(QGraphicsRectItem.ItemIsSelectable) # Nanti bisa ditambah ItemIsMovable
        
        # Hitung Geometri
        start_pixel = float(layer_data.properties.get("start_time", 0.0)) * ZOOM_LEVEL
        duration_pixel = float(layer_data.properties.get("duration", 5.0)) * ZOOM_LEVEL
        y_pos = (row_index * TRACK_HEIGHT) + HEADER_HEIGHT + 5
        
        self.setRect(0, 0, duration_pixel, TRACK_HEIGHT - 10)
        self.setPos(start_pixel, y_pos)
        
        # Styling
        color = "#3498db" if layer_data.type == "video" else "#e67e22" if layer_data.type == "text" else "#9b59b6"
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.NoPen))
        self.setOpacity(0.8)
        
        # Label Nama
        self.text = QGraphicsTextItem(layer_data.name, self)
        self.text.setDefaultTextColor(QColor("white"))
        self.text.setFont(QFont("Arial", 8))
        self.text.setPos(5, 5)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemSelectedChange:
            # Highlight saat dipilih
            self.setOpacity(1.0 if value else 0.8)
            self.setPen(QPen(QColor("white"), 2) if value else QPen(Qt.NoPen))
        return super().itemChange(change, value)

class LayerPanel(QGraphicsView):
    """
    Timeline Panel: Menggantikan QListWidget lama.
    Sekarang menampilkan layer secara horizontal (Waktu).
    """
    # Signal untuk Controller
    sig_request_seek = Signal(float)
    sig_layer_selected = Signal(str)
    
    # Signal Legacy (Agar tidak error di Binder, meski belum diimplementasi full drag-dropnya)
    sig_request_add = Signal(str) 
    sig_request_delete = Signal()
    sig_request_reorder = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setBackgroundBrush(QBrush(QColor("#2c3e50")))
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Komponen Playhead (Garis Merah)
        self.playhead = QGraphicsLineItem()
        self.playhead.setPen(QPen(QColor("#e74c3c"), 2))
        self.playhead.setZValue(999) # Selalu paling atas
        self.scene.addItem(self.playhead)
        
        self.clip_registry = {} # Map ID -> TimelineClipItem

    def set_duration_view(self, duration_sec: float):
        """Mengatur panjang kanvas timeline"""
        width = duration_sec * ZOOM_LEVEL + 500 # Extra space
        height = max(500, len(self.clip_registry) * TRACK_HEIGHT + HEADER_HEIGHT)
        self.scene.setSceneRect(0, 0, width, height)
        
        # Update tinggi playhead
        self.playhead.setLine(0, 0, 0, height)

    def update_playhead(self, t: float):
        """Dipanggil setiap frame untuk menggeser garis merah"""
        x_pos = t * ZOOM_LEVEL
        self.playhead.setX(x_pos)
        
        # Auto scroll jika playhead keluar layar (Opsional)
        # self.ensureVisible(self.playhead)

    # --- CRUD VISUAL ---

    def add_item_visual(self, layer_id, name):
        # Timeline butuh data lengkap (start/duration), bukan cuma ID/Nama.
        # Karena Binder lama hanya kirim ID/Nama, kita tunggu 'sync_full' atau
        # kita biarkan kosong dulu sampai 'on_property_changed' atau 'reload'.
        # -> Strategi: Kita akan update Binder untuk kirim LayerData object penuh.
        pass 

    def sync_all_layers(self, layers: list):
        """Reset total dan gambar ulang semua layer (Paling aman)"""
        # Hapus semua clip (kecuali playhead)
        for item in self.clip_registry.values():
            self.scene.removeItem(item)
        self.clip_registry.clear()
        
        # Gambar ulang
        max_duration = 0
        for i, layer_data in enumerate(layers):
            clip = TimelineClipItem(layer_data, i)
            self.scene.addItem(clip)
            self.clip_registry[layer_data.id] = clip
            
            # Cek durasi max
            end_time = float(layer_data.properties.get("start_time", 0)) + float(layer_data.properties.get("duration", 5))
            if end_time > max_duration: max_duration = end_time
            
        self.set_duration_view(max(10.0, max_duration))

    def select_item_visual(self, layer_id):
        self.scene.clearSelection()
        if layer_id in self.clip_registry:
            self.clip_registry[layer_id].setSelected(True)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        
        # 1. Deteksi Klik di Ruler/Background (Seeking)
        # Jika tidak mengenai ClipItem, berarti user mau geser Playhead
        item = self.itemAt(event.pos())
        if not isinstance(item, TimelineClipItem):
            scene_pos = self.mapToScene(event.pos())
            t = max(0, scene_pos.x() / ZOOM_LEVEL)
            self.sig_request_seek.emit(t)
            self.update_playhead(t)
            
        # 2. Deteksi Klik di Clip (Selection)
        else:
            self.sig_layer_selected.emit(item.layer_id)