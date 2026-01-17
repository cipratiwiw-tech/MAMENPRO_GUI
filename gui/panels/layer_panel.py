# gui/panels/layer_panel.py

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QFont, QPainter, QWheelEvent, QPolygonF

# KONSTANTA TAMPILAN
TRACK_HEIGHT = 50       # Tinggi per track (lebih lega)
HEADER_HEIGHT = 40      # Tinggi Ruler
RULER_BG = "#1e1e1e"
TRACK_BG_EVEN = "#282c34" # Warna Track Genap (Gelap)
TRACK_BG_ODD = "#21252b"  # Warna Track Ganjil (Agak Terang)
GRID_COLOR = "#3e4451"

class TimelineClipItem(QGraphicsRectItem):
    """
    Visual Clip:
    - Lebar = Durasi asli * Zoom
    - Posisi X = Start Time * Zoom
    - Posisi Y = Sesuai Index Track
    """
    def __init__(self, layer_data, row_index, parent_view):
        super().__init__()
        self.layer_id = layer_data.id
        self.layer_name = layer_data.name
        self.parent_view = parent_view 
        self.row_index = row_index
        
        # Data Waktu (Single Source of Truth)
        self.current_start_time = float(layer_data.properties.get("start_time", 0.0))
        self.duration = float(layer_data.properties.get("duration", 5.0))

        # Setup Visual
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Warna Clip Berdasarkan Tipe
        if layer_data.type == "video":
            base_color = "#3498db" # Biru
        elif layer_data.type == "text":
            base_color = "#e67e22" # Orange
        elif layer_data.type == "audio":
            base_color = "#2ecc71" # Hijau
        else:
            base_color = "#9b59b6" # Ungu

        self.brush_color = QColor(base_color)
        self.setBrush(QBrush(self.brush_color.darker(110)))
        
        # Border clip biar tegas
        self.setPen(QPen(QColor("#ffffff"), 1))
        self.setOpacity(0.9)
        
        # Label Nama Clip
        self.text = QGraphicsTextItem(self.layer_name, self)
        self.text.setDefaultTextColor(QColor("white"))
        font = QFont("Segoe UI", 9)
        font.setBold(True)
        self.text.setFont(font)
        self.text.setPos(5, 0) # Padding text

        # Dragging State
        self._is_dragging = False
        self._drag_start_x = 0
        self._initial_pos_x = 0
        
        # Hitung Posisi Awal
        self.update_geometry_from_zoom()

    def update_geometry_from_zoom(self):
        """Kunci Logika: Sinkronisasi Ruler & Track"""
        zoom = self.parent_view.zoom_level
        
        # 1. Hitung Posisi Horizontal (Waktu)
        x_pos = self.current_start_time * zoom
        width = self.duration * zoom
        
        # 2. Hitung Posisi Vertikal (Track)
        # Clip dimulai SETELAH Header (Ruler)
        # Ditambah padding kecil (2px) biar tidak nempel garis
        y_pos = HEADER_HEIGHT + (self.row_index * TRACK_HEIGHT) + 2
        height = TRACK_HEIGHT - 4 

        self.setRect(0, 0, width, height)
        self.setPos(x_pos, y_pos)

        # Update lebar text agar tidak keluar clip (opsional clipping)
        self.text.setTextWidth(width - 10)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_start_x = event.scenePos().x()
            self._initial_pos_x = self.pos().x()
            self.setOpacity(0.6) 
            self.setCursor(Qt.ClosedHandCursor)
            self.parent_view.sig_layer_selected.emit(self.layer_id)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            # 1. Hitung Delta X
            current_x = event.scenePos().x()
            delta = current_x - self._drag_start_x
            new_x = self._initial_pos_x + delta
            if new_x < 0: new_x = 0
            
            # 2. Kunci Y (Hanya geser horizontal, tidak bisa pindah track via drag mouse visual)
            # (Fitur pindah track biasanya butuh logika reorder list di controller)
            self.setPos(new_x, self.y())
            
            # 3. Tooltip Waktu Realtime
            new_time = new_x / self.parent_view.zoom_level
            self.setToolTip(f"Start: {self.parent_view._format_time(new_time)}")
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_dragging:
            self._is_dragging = False
            self.setOpacity(0.9 if not self.isSelected() else 1.0)
            self.setCursor(Qt.ArrowCursor)
            
            # Hitung waktu akhir
            final_pixel_x = self.pos().x()
            new_start_time = final_pixel_x / self.parent_view.zoom_level
            
            # Request update data ke Controller
            if abs(new_start_time - self.current_start_time) > 0.01:
                self.parent_view.sig_request_move.emit(self.layer_id, new_start_time)
            else:
                # Snap back visual jika pergeseran terlalu kecil (misal tidak sengaja)
                self.update_geometry_from_zoom()

        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemSelectedChange:
            # Highlight border saat dipilih
            if value:
                self.setPen(QPen(QColor("#00AEEF"), 2)) # Cyan border
                self.setZValue(10) # Bawa ke depan
            else:
                self.setPen(QPen(QColor("#ffffff"), 1))
                self.setZValue(0)
        return super().itemChange(change, value)


class LayerPanel(QGraphicsView):
    # Signals
    sig_request_seek = Signal(float)       
    sig_layer_selected = Signal(str)       
    sig_request_move = Signal(str, float)
    
    # Legacy Signals (Required by Binder)
    sig_request_add = Signal(str)          
    sig_request_delete = Signal()
    sig_request_reorder = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup Scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Setup Viewport
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        
        # Scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # State Zoom & Data
        self.zoom_level = 50.0  # Pixels per second
        self.min_zoom = 5.0
        self.max_zoom = 400.0
        
        self.clip_registry = {}
        self.last_layers_data = [] 

        # Playhead (Garis Merah)
        self.playhead = QGraphicsLineItem()
        self.playhead.setPen(QPen(QColor("#ff0000"), 1.5))
        self.playhead.setZValue(9999) 
        self.scene.addItem(self.playhead)
        
        # Inisialisasi area scene awal
        self.scene.setSceneRect(0, 0, 2000, 500)

    # ==========================================
    # 1. RENDERING BACKGROUND (TRACKS)
    # ==========================================
    def drawBackground(self, painter: QPainter, rect: QRectF):
        """
        Menggambar Track Zebra (Belang-belang) di area canvas.
        Ini digambar di koordinat Scene (bukan viewport).
        """
        super().drawBackground(painter, rect)
        
        # Fill Warna Dasar
        painter.fillRect(rect, QColor(TRACK_BG_ODD))
        
        # Hitung area visible vertikal
        top = int(rect.top())
        bottom = int(rect.bottom())
        left = int(rect.left())
        right = int(rect.right())
        
        # Mulai menggambar track dari bawah Header
        start_y = HEADER_HEIGHT
        
        # Cari index track pertama yang terlihat
        first_track_idx = max(0, (top - HEADER_HEIGHT) // TRACK_HEIGHT)
        
        current_y = HEADER_HEIGHT + (first_track_idx * TRACK_HEIGHT)
        track_idx = first_track_idx

        while current_y < bottom:
            # Gambar Background Track Genap (Lebih gelap)
            if track_idx % 2 == 0:
                track_rect = QRectF(left, current_y, right - left, TRACK_HEIGHT)
                painter.fillRect(track_rect, QColor(TRACK_BG_EVEN))
            
            # Gambar Garis Pemisah (Grid Horizontal)
            painter.setPen(QPen(QColor(GRID_COLOR), 1))
            painter.drawLine(left, current_y, right, current_y)
            
            # (Opsional) Tulis Nomor Track di pojok kiri (hanya hiasan)
            # painter.setPen(QColor("#555"))
            # painter.drawText(left + 5, current_y + 15, f"V{track_idx + 1}")

            current_y += TRACK_HEIGHT
            track_idx += 1
            
        # Gambar Garis Waktu Vertikal (Grid Detik)
        # Logika sama dengan Ruler tapi transparansi rendah
        min_pixels_per_tick = 100
        step = self._calculate_adaptive_step(min_pixels_per_tick / self.zoom_level)
        
        start_t = int(left / self.zoom_level / step) * step
        t = start_t
        while True:
            x = t * self.zoom_level
            if x > right: break
            if x >= left:
                painter.setPen(QPen(QColor(GRID_COLOR), 1, Qt.DotLine))
                painter.drawLine(x, max(top, HEADER_HEIGHT), x, bottom)
            t += step

    # ==========================================
    # 2. RENDERING FOREGROUND (RULER)
    # ==========================================
    def drawForeground(self, painter: QPainter, rect: QRectF):
        """
        Menggambar Ruler Sticky di atas Track.
        Posisi Y relatif terhadap Viewport (rect.top).
        """
        super().drawForeground(painter, rect)
        
        # Area Ruler Sticky
        ruler_rect = QRectF(rect.left(), rect.top(), rect.width(), HEADER_HEIGHT)
        
        # Background Ruler
        painter.fillRect(ruler_rect, QColor(RULER_BG))
        
        # Garis Bawah Ruler
        painter.setPen(QPen(QColor("#000"), 1))
        painter.drawLine(ruler_rect.bottomLeft(), ruler_rect.bottomRight())
        
        # Kalkulasi Tick Adaptive
        min_pixels_per_tick = 80
        step = self._calculate_adaptive_step(min_pixels_per_tick / self.zoom_level)
        
        start_x = rect.left()
        end_x = rect.right()
        
        start_t = int(start_x / self.zoom_level / step) * step
        current_t = start_t
        
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        
        while True:
            pos_x = current_t * self.zoom_level
            if pos_x > end_x: break
            
            if pos_x >= start_x:
                # Garis Tick Besar
                painter.setPen(QPen(QColor("#ccc"), 1))
                painter.drawLine(pos_x, rect.top() + 20, pos_x, rect.top() + HEADER_HEIGHT)
                
                # Teks Waktu
                time_str = self._format_time(current_t)
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(time_str)
                painter.setPen(QColor("#ccc"))
                painter.drawText(pos_x - tw/2, rect.top() + 15, time_str)
                
                # Sub-ticks (Garis kecil)
                self._draw_sub_ticks(painter, rect.top(), pos_x, step, self.zoom_level)
                
            current_t += step

    # ==========================================
    # HELPERS
    # ==========================================
    def _calculate_adaptive_step(self, min_seconds):
        presets = [0.1, 0.5, 1.0, 5.0, 10.0, 15.0, 30.0, 60.0]
        for p in presets:
            if p >= min_seconds: return p
        return 300.0

    def _draw_sub_ticks(self, painter, top_y, major_x, major_step, zoom):
        sub_count = 5
        sub_step_px = (major_step * zoom) / sub_count
        painter.setPen(QPen(QColor("#666"), 1))
        for i in range(1, sub_count):
            sub_x = major_x + (i * sub_step_px)
            painter.drawLine(sub_x, top_y + 28, sub_x, top_y + HEADER_HEIGHT)

    def _format_time(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        if self.zoom_level > 80:
            frame = int((seconds - int(seconds)) * 30)
            return f"{m:02d}:{s:02d}:{frame:02d}"
        return f"{m:02d}:{s:02d}"

    # ==========================================
    # INTERACTION & LOGIC
    # ==========================================
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            factor = 1.1 if delta > 0 else 0.9
            self.set_zoom(self.zoom_level * factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def set_zoom(self, new_level):
        self.zoom_level = max(self.min_zoom, min(new_level, self.max_zoom))
        self.sync_all_layers(self.last_layers_data)
        
        # Update posisi Playhead saat zoom
        # (Idealnya playhead simpan waktu, bukan X, tapi ini quick fix)
        # Kita trigger repaint saja, posisi playhead di-update via update_playhead dari controller
        self.viewport().update()

    def sync_all_layers(self, layers: list):
        self.last_layers_data = layers
        
        # Bersihkan scene item clip (tapi jangan hapus playhead)
        for item in self.clip_registry.values():
            self.scene.removeItem(item)
        self.clip_registry.clear()
        
        max_duration = 0
        
        # Re-create Clips
        for i, layer_data in enumerate(layers):
            clip = TimelineClipItem(layer_data, i, self)
            self.scene.addItem(clip)
            self.clip_registry[layer_data.id] = clip
            
            end_t = float(layer_data.properties.get("start_time", 0)) + float(layer_data.properties.get("duration", 0))
            if end_t > max_duration: max_duration = end_t
            
        # Update ukuran Scene agar bisa scroll
        # Lebar = Durasi + padding
        # Tinggi = Header + (Jumlah Track * Tinggi Track) + Padding Bawah
        width = max(30.0, max_duration) * self.zoom_level + 500
        height = HEADER_HEIGHT + (len(layers) * TRACK_HEIGHT) + 200 # Extra space for new tracks
        
        # Minimal tinggi 10 track biar track kosong tergambar
        height = max(height, HEADER_HEIGHT + (10 * TRACK_HEIGHT))
        
        self.scene.setSceneRect(0, 0, width, height)
        self.playhead.setLine(0, HEADER_HEIGHT, 0, height)
        self.viewport().update()

    def update_playhead(self, t: float):
        x = t * self.zoom_level
        self.playhead.setX(x)
        # Auto scroll jika playhead di ujung kanan layar
        visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        if x > visible_rect.right() - 50:
             self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + 50)

    # Mouse Events (Seek on Ruler)
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        
        sp = self.mapToScene(event.pos())
        top_vis = self.mapToScene(0, 0).y()
        
        # Cek apakah klik di area Header Ruler
        if sp.y() < (top_vis + HEADER_HEIGHT):
            # Seek Mode
            t = max(0, sp.x() / self.zoom_level)
            self.sig_request_seek.emit(t)
            self.update_playhead(t)

    # Placeholder Binder
    def add_item_visual(self, *args): pass
    def remove_item_visual(self, *args): pass
    def clear_visual(self): pass
    def select_item_visual(self, layer_id):
        self.scene.clearSelection()
        if layer_id in self.clip_registry:
            self.clip_registry[layer_id].setSelected(True)