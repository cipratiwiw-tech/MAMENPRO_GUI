# gui/panels/layer_panel.py

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QBrush, QColor, QPen, QFont

ZOOM_LEVEL = 50.0  # 1 detik = 50 pixel
TRACK_HEIGHT = 40
HEADER_HEIGHT = 30

class TimelineClipItem(QGraphicsRectItem):
    """
    Representasi Visual dari Layer.
    Menerapkan 'Safe Dragging': Visual bergerak, tapi Data menunggu Controller.
    """
    def __init__(self, layer_data, row_index, parent_view):
        super().__init__()
        self.layer_id = layer_data.id
        self.layer_name = layer_data.name
        self.parent_view = parent_view 
        
        self.current_start_time = float(layer_data.properties.get("start_time", 0.0))
        
        # Enable Mouse Events
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Hitung Geometri Awal
        start_pixel = self.current_start_time * ZOOM_LEVEL
        duration_pixel = float(layer_data.properties.get("duration", 5.0)) * ZOOM_LEVEL
        self.fixed_y = (row_index * TRACK_HEIGHT) + HEADER_HEIGHT + 5
        
        self.setRect(0, 0, duration_pixel, TRACK_HEIGHT - 10)
        self.setPos(start_pixel, self.fixed_y)
        
        # Styling
        color = "#3498db" if layer_data.type == "video" else "#e67e22" if layer_data.type == "text" else "#9b59b6"
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.NoPen))
        self.setOpacity(0.8)
        
        # Label Nama
        self.text = QGraphicsTextItem(self.layer_name, self)
        self.text.setDefaultTextColor(QColor("white"))
        self.text.setFont(QFont("Arial", 8))
        self.text.setPos(5, 5)

        # Dragging State
        self._is_dragging = False
        self._drag_start_x = 0
        self._initial_pos_x = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_start_x = event.scenePos().x()
            self._initial_pos_x = self.pos().x()
            self.setOpacity(0.5) 
            self.setCursor(Qt.ClosedHandCursor)
            self.parent_view.sig_layer_selected.emit(self.layer_id)
        super().mousePressEvent(event)

    # [PERBAIKAN DI SINI] Urutan parameter: (self, event)
    def mouseMoveEvent(self, event):
        if self._is_dragging:
            # 1. Hitung Pergeseran Pixel
            current_x = event.scenePos().x()
            delta = current_x - self._drag_start_x
            new_x = self._initial_pos_x + delta
            
            # 2. Batasi agar tidak minus
            if new_x < 0: new_x = 0
            
            # 3. Pindahkan Visual (Sumbu Y KUNCI)
            self.setPos(new_x, self.fixed_y)
            
            # 4. Tooltip waktu
            new_time = new_x / ZOOM_LEVEL
            self.setToolTip(f"{new_time:.2f}s")
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_dragging:
            self._is_dragging = False
            self.setOpacity(0.8 if not self.isSelected() else 1.0)
            self.setCursor(Qt.ArrowCursor)
            
            final_pixel_x = self.pos().x()
            new_start_time = final_pixel_x / ZOOM_LEVEL
            
            if abs(new_start_time - self.current_start_time) > 0.01:
                # Ajukan proposal pindah ke Controller
                self.parent_view.sig_request_move.emit(self.layer_id, new_start_time)
            else:
                pass

        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemSelectedChange:
            self.setOpacity(1.0 if value else 0.8)
            self.setPen(QPen(QColor("white"), 2) if value else QPen(Qt.NoPen))
        return super().itemChange(change, value)



class LayerPanel(QGraphicsView):
    # ==========================================
    # 1. SIGNALS (HARUS LENGKAP)
    # ==========================================
    
    # Signal Timeline Baru
    sig_request_seek = Signal(float)       # Minta geser waktu
    sig_layer_selected = Signal(str)       # Layer dipilih
    sig_request_move = Signal(str, float)  # Drag & Drop (Move Proposal)

    # Signal Legacy (WAJIB ADA agar Binder tidak Error)
    # Walaupun tombolnya belum ada di Timeline, Binder butuh koneksi ini
    sig_request_add = Signal(str)          
    sig_request_delete = Signal()
    sig_request_reorder = Signal(int, int)

    # ==========================================
    # 2. INITIALIZATION
    # ==========================================
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setBackgroundBrush(QBrush(QColor("#2c3e50")))
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Komponen Playhead (Garis Merah)
        self.playhead = QGraphicsLineItem()
        self.playhead.setPen(QPen(QColor("#e74c3c"), 2))
        self.playhead.setZValue(999) 
        self.scene.addItem(self.playhead)
        
        self.clip_registry = {}

    def set_duration_view(self, duration_sec: float):
        width = duration_sec * ZOOM_LEVEL + 500 
        height = max(500, len(self.clip_registry) * TRACK_HEIGHT + HEADER_HEIGHT)
        self.scene.setSceneRect(0, 0, width, height)
        self.playhead.setLine(0, 0, 0, height)

    def update_playhead(self, t: float):
        x_pos = t * ZOOM_LEVEL
        self.playhead.setX(x_pos)

    def sync_all_layers(self, layers: list):
        """Reset total dan gambar ulang semua layer (Single Source of Truth)"""
        # Hapus clip lama
        for item in self.clip_registry.values():
            self.scene.removeItem(item)
        self.clip_registry.clear()
        
        # Gambar ulang berdasarkan data Controller
        max_duration = 0
        for i, layer_data in enumerate(layers):
            # Pass 'self' sebagai parent_view agar clip bisa emit signal panel
            clip = TimelineClipItem(layer_data, i, self) 
            self.scene.addItem(clip)
            self.clip_registry[layer_data.id] = clip
            
            end_time = float(layer_data.properties.get("start_time", 0)) + float(layer_data.properties.get("duration", 5))
            if end_time > max_duration: max_duration = end_time
            
        self.set_duration_view(max(10.0, max_duration))

    # ... (Method add_item_visual dll biarkan kosong/pass dulu) ...
    def add_item_visual(self, layer_id, name): pass
    def remove_item_visual(self, layer_id): pass
    def clear_visual(self): pass

    def select_item_visual(self, layer_id):
        self.scene.clearSelection()
        if layer_id in self.clip_registry:
            self.clip_registry[layer_id].setSelected(True)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        item = self.itemAt(event.pos())
        if not isinstance(item, TimelineClipItem):
            scene_pos = self.mapToScene(event.pos())
            t = max(0, scene_pos.x() / ZOOM_LEVEL)
            self.sig_request_seek.emit(t)
            self.update_playhead(t)