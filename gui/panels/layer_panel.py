# gui/panels/layer_panel.py

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QFont, QPainter, QWheelEvent

# ==========================================
# KONSTANTA TAMPILAN
# ==========================================
HEADER_HEIGHT = 40      
RULER_BG = "#1e1e1e"
TRACK_BG_EVEN = "#282c34" 
TRACK_BG_ODD = "#21252b"  
GRID_COLOR = "#3e4451"

class TimelineClipItem(QGraphicsRectItem):
    """
    Item visual yang merepresentasikan Clip di Timeline.
    Posisi dan ukurannya responsif terhadap zoom_level dan track_height parent.
    """
    def __init__(self, layer_data, row_index, parent_view):
        super().__init__()
        self.layer_id = layer_data.id
        self.layer_name = layer_data.name
        self.parent_view = parent_view 
        self.row_index = row_index
        
        self.current_start_time = float(layer_data.properties.get("start_time", 0.0))
        self.duration = float(layer_data.properties.get("duration", 5.0))

        # Setup Visual
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Warna Clip Berdasarkan Tipe
        if layer_data.type == "video": base_color = "#3498db"
        elif layer_data.type == "text": base_color = "#e67e22"
        elif layer_data.type == "audio": base_color = "#2ecc71"
        else: base_color = "#9b59b6"

        self.brush_color = QColor(base_color)
        self.setBrush(QBrush(self.brush_color.darker(110)))
        self.setPen(QPen(QColor("#ffffff"), 1))
        self.setOpacity(0.9)
        
        # Label Nama Clip
        self.text = QGraphicsTextItem(self.layer_name, self)
        self.text.setDefaultTextColor(QColor("white"))
        self.font_small = QFont("Segoe UI", 8)
        self.text.setFont(self.font_small)
        self.text.setPos(5, 0)

        # Dragging State
        self._is_dragging = False
        self._drag_start_x = 0
        self._initial_pos_x = 0
        
        # Init Geometri
        self.update_geometry()

    def update_geometry(self):
        """Update posisi & ukuran pixel berdasarkan state zoom panel"""
        zoom = self.parent_view.zoom_level
        t_height = self.parent_view.track_height 
        
        # Hitung X (Waktu)
        x_pos = self.current_start_time * zoom
        width = self.duration * zoom
        
        # Hitung Y (Track)
        y_pos = HEADER_HEIGHT + (self.row_index * t_height) + 1
        height = t_height - 2 

        self.setRect(0, 0, width, height)
        self.setPos(x_pos, y_pos)

        # Sembunyikan teks jika track terlalu gepeng
        if t_height < 25:
            self.text.setVisible(False)
        else:
            self.text.setVisible(True)
            self.text.setTextWidth(width - 5)

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
            # Logic Drag Horizontal Saja
            current_x = event.scenePos().x()
            delta = current_x - self._drag_start_x
            new_x = max(0, self._initial_pos_x + delta)
            
            self.setPos(new_x, self.y())
            
            new_time = new_x / self.parent_view.zoom_level
            self.setToolTip(f"Start: {self.parent_view._format_time(new_time)}")
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_dragging:
            self._is_dragging = False
            self.setOpacity(0.9 if not self.isSelected() else 1.0)
            self.setCursor(Qt.ArrowCursor)
            
            final_pixel_x = self.pos().x()
            new_start_time = final_pixel_x / self.parent_view.zoom_level
            
            # Request pindah ke Controller hanya jika geser signifikan
            if abs(new_start_time - self.current_start_time) > 0.01:
                self.parent_view.sig_request_move.emit(self.layer_id, new_start_time)
            else:
                self.update_geometry() # Snap back jika tidak jadi pindah
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemSelectedChange:
            if value:
                self.setPen(QPen(QColor("#00AEEF"), 2))
                self.setZValue(10) # Bawa ke depan saat dipilih
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
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # View Settings
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        
        # Scrollbars selalu on agar tidak flickering saat layout berubah
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # 🔥 CRITICAL: Matikan Auto Anchor Qt
        # Kita akan menghitung scrollbar secara manual agar presisi (Sticky Zoom)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)

        # STATE ZOOM
        self.zoom_level = 50.0 
        self.min_zoom = 5.0
        self.max_zoom = 600.0 # Rentang zoom lebih luas
        
        # STATE TRACK HEIGHT
        self.track_height = 50 
        self.min_track_height = 20
        self.max_track_height = 150

        self.clip_registry = {}
        self.last_layers_data = [] 

        # Playhead (Garis Merah)
        self.playhead = QGraphicsLineItem()
        self.playhead.setPen(QPen(QColor("#ff0000"), 1.5))
        self.playhead.setZValue(9999) 
        self.scene.addItem(self.playhead)
        
        # Init Scene Awal
        self.scene.setSceneRect(0, 0, 2000, 500)

    # ==========================================
    # INPUT HANDLER (STICKY ZOOM LOGIC)
    # ==========================================
    def wheelEvent(self, event: QWheelEvent):
        """
        Logic Zoom yang 'Menempel' (Anchored) pada posisi mouse.
        Menggunakan Raw Calculation untuk menghindari clamping scene rect.
        """
        modifiers = event.modifiers()
        delta = event.angleDelta().y()
        
        # Ambil posisi mouse relatif terhadap viewport (layar)
        # Bukan mapToScene, tapi raw pixel
        mouse_x = event.position().x()
        mouse_y = event.position().y()
        
        # Ambil posisi scrollbar saat ini
        scroll_x = self.horizontalScrollBar().value()
        scroll_y = self.verticalScrollBar().value()
        
        if modifiers == Qt.ControlModifier:
            # --- HORIZONTAL ZOOM (WAKTU) ---
            event.accept()
            
            # 1. Hitung titik waktu (detik) tepat di bawah kursor mouse
            # SceneX = ScrollX + MouseX
            scene_x_before = scroll_x + mouse_x
            time_under_mouse = scene_x_before / self.zoom_level
            
            # 2. Update Zoom Level
            factor = 1.15 if delta > 0 else 0.85 # Smooth factor
            new_zoom = max(self.min_zoom, min(self.zoom_level * factor, self.max_zoom))
            
            if new_zoom != self.zoom_level:
                self.zoom_level = new_zoom
                
                # 3. Hitung posisi SceneX BARU untuk waktu yang sama
                new_scene_x = time_under_mouse * new_zoom
                
                # 4. Hitung target Scrollbar agar MouseX tetap di posisi yang sama
                # MouseX = NewSceneX - NewScrollX  =>  NewScrollX = NewSceneX - MouseX
                target_scroll_x = int(new_scene_x - mouse_x)
                
                # 5. Refresh Layout dengan 'Minimum Width Needed'
                # Ini KUNCI agar tidak loncat ke 0. SceneRect dipaksa membesar
                # untuk menampung posisi scroll target, meskipun di area kosong.
                min_width = target_scroll_x + self.viewport().width() + 1000
                self._refresh_layout(min_width_needed=min_width)
                
                # 6. Apply Scroll
                self.horizontalScrollBar().setValue(target_scroll_x)
            
        elif modifiers == Qt.ShiftModifier:
            # --- VERTICAL ZOOM (TINGGI TRACK) ---
            event.accept()
            
            # 1. Hitung titik Track (rasio) di bawah kursor mouse
            scene_y_before = scroll_y + mouse_y
            
            # Kurangi header karena header tidak di-zoom
            track_content_y = scene_y_before - HEADER_HEIGHT
            # Jika mouse di header, anggap di track 0 paling atas
            track_content_y = max(0, track_content_y)
            
            track_ratio_under_mouse = track_content_y / self.track_height
            
            # 2. Update Track Height
            step = 5 if delta > 0 else -5
            new_height = max(self.min_track_height, min(self.track_height + step, self.max_track_height))
            
            if new_height != self.track_height:
                self.track_height = new_height
                
                # 3. Hitung target Scrollbar Y
                new_track_content_y = track_ratio_under_mouse * new_height
                new_scene_y = HEADER_HEIGHT + new_track_content_y
                target_scroll_y = int(new_scene_y - mouse_y)
                
                # 4. Refresh Layout dengan 'Minimum Height Needed'
                min_height = target_scroll_y + self.viewport().height() + 500
                self._refresh_layout(min_height_needed=min_height)
                
                # 5. Apply Scroll
                self.verticalScrollBar().setValue(target_scroll_y)
            
        else:
            super().wheelEvent(event)

    def _refresh_layout(self, min_width_needed=0, min_height_needed=0):
        """Update geometri item dan ukuran scene"""
        
        # 1. Update posisi/ukuran setiap Clip
        for clip in self.clip_registry.values():
            clip.update_geometry()
            
        # 2. Hitung Ukuran Konten Real
        layer_count = len(self.last_layers_data)
        max_duration = 0
        for l in self.last_layers_data:
            end = float(l.properties.get("start_time", 0)) + float(l.properties.get("duration", 0))
            if end > max_duration: max_duration = end

        # 3. Hitung Ukuran Scene
        # Gunakan max() antara konten real VS kebutuhan scroll (min_width_needed)
        # Buffer +1000 px agar user nyaman scroll ke area kosong kanan
        content_width = max(30.0, max_duration) * self.zoom_level + 1000
        content_height = HEADER_HEIGHT + (max(10, layer_count) * self.track_height) + 200
        
        final_width = max(content_width, min_width_needed)
        final_height = max(content_height, min_height_needed)
        
        # 4. Set Scene Rect
        # Mulai dari 0,0. Lebar dan Tinggi dinamis.
        self.scene.setSceneRect(0, 0, final_width, final_height)
        
        # Perpanjang garis Playhead
        self.playhead.setLine(0, HEADER_HEIGHT, 0, final_height)
        
        # Force Repaint viewport (untuk update Grid Background)
        self.viewport().update()

    # ==========================================
    # RENDERING BACKGROUND (Zebra Tracks)
    # ==========================================
    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        painter.fillRect(rect, QColor(TRACK_BG_ODD))
        
        top = int(rect.top())
        bottom = int(rect.bottom())
        left = int(rect.left())
        right = int(rect.right())
        
        th = self.track_height
        
        # Optimasi: Gambar hanya track yang terlihat
        first_track_idx = max(0, (top - HEADER_HEIGHT) // th)
        current_y = HEADER_HEIGHT + (first_track_idx * th)
        track_idx = first_track_idx

        while current_y < bottom:
            # Track Genap lebih gelap
            if track_idx % 2 == 0:
                track_rect = QRectF(left, current_y, right - left, th)
                painter.fillRect(track_rect, QColor(TRACK_BG_EVEN))
            
            # Garis Horizontal
            painter.setPen(QPen(QColor(GRID_COLOR), 1))
            painter.drawLine(left, current_y, right, current_y)

            current_y += th
            track_idx += 1
            
        # Grid Waktu Vertikal (Adaptive)
        min_px = 100
        step = self._calculate_adaptive_step(min_px / self.zoom_level)
        
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
    # RENDERING FOREGROUND (Ruler Sticky)
    # ==========================================
    def drawForeground(self, painter: QPainter, rect: QRectF):
        super().drawForeground(painter, rect)
        
        # Area Ruler (Selalu di atas viewport)
        ruler_rect = QRectF(rect.left(), rect.top(), rect.width(), HEADER_HEIGHT)
        painter.fillRect(ruler_rect, QColor(RULER_BG))
        
        # Garis Batas Bawah Ruler
        painter.setPen(QPen(QColor("#000"), 1))
        painter.drawLine(ruler_rect.bottomLeft(), ruler_rect.bottomRight())
        
        min_px = 80
        step = self._calculate_adaptive_step(min_px / self.zoom_level)
        
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
                # Tick Besar
                painter.setPen(QPen(QColor("#ccc"), 1))
                painter.drawLine(pos_x, rect.top() + 20, pos_x, rect.top() + HEADER_HEIGHT)
                
                # Teks Waktu
                time_str = self._format_time(current_t)
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(time_str)
                painter.setPen(QColor("#ccc"))
                painter.drawText(pos_x - tw/2, rect.top() + 15, time_str)
                
                # Tick Kecil
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

    def sync_all_layers(self, layers: list):
        self.last_layers_data = layers
        # Reset visual item
        for item in self.clip_registry.values():
            self.scene.removeItem(item)
        self.clip_registry.clear()
        
        # Create new visual items
        for i, layer_data in enumerate(layers):
            clip = TimelineClipItem(layer_data, i, self)
            self.scene.addItem(clip)
            self.clip_registry[layer_data.id] = clip
            
        self._refresh_layout()

    def update_playhead(self, t: float):
        x = t * self.zoom_level
        self.playhead.setX(x)
        # Auto scroll kalau playhead keluar kanan, tapi tidak agresif
        visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        if x > visible_rect.right() - 50:
             self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + 50)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        # Seek Logic via Ruler Click
        sp = self.mapToScene(event.pos())
        top_vis = self.mapToScene(0, 0).y() # Top scene visible coordinate
        
        # Jika klik di area Header Ruler
        if sp.y() < (top_vis + HEADER_HEIGHT):
            t = max(0, sp.x() / self.zoom_level)
            self.sig_request_seek.emit(t)
            self.update_playhead(t)

    # Binder requirements (Stubs)
    def add_item_visual(self, *args): pass
    def remove_item_visual(self, *args): pass
    def clear_visual(self): pass
    def select_item_visual(self, layer_id):
        self.scene.clearSelection()
        if layer_id in self.clip_registry:
            self.clip_registry[layer_id].setSelected(True)