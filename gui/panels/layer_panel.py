# gui/panels/layer_panel.py

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QFont, QPainter, QWheelEvent
import math

# ==========================================
# KONSTANTA TAMPILAN
# ==========================================
HEADER_HEIGHT = 30          
TRACK_HEADER_WIDTH = 120    
RULER_BG = "#1e1e1e"
SIDEBAR_BG = "#21252b"      
TRACK_BG_EVEN = "#282c34" 
TRACK_BG_ODD = "#262a30"  
GRID_COLOR = "#3e4451"

# LOGIKA WAKTU
FPS = 30.0 

class TimelineClipItem(QGraphicsRectItem):
    def __init__(self, layer_data, row_index, parent_view):
        super().__init__()
        self.layer_id = layer_data.id
        self.layer_name = layer_data.name
        self.parent_view = parent_view 
        self.row_index = row_index 
        
        self.current_start_time = float(layer_data.properties.get("start_time", 0.0))
        self.duration = float(layer_data.properties.get("duration", 5.0))

        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Warna Clip
        if layer_data.type == "video": base_color = "#3498db"
        elif layer_data.type == "text": base_color = "#e67e22"
        elif layer_data.type == "audio": base_color = "#2ecc71"
        else: base_color = "#9b59b6"

        self.brush_color = QColor(base_color)
        self.setBrush(QBrush(self.brush_color.darker(110)))
        self.setPen(QPen(QColor("#ffffff"), 1))
        self.setOpacity(0.9)
        
        self.text = QGraphicsTextItem(self.layer_name, self)
        self.text.setDefaultTextColor(QColor("white"))
        self.text.setFont(QFont("Segoe UI", 8))
        self.text.setPos(5, 0)

        # Dragging State
        self._is_dragging = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._initial_pos_x = 0
        self._initial_pos_y = 0
        self._preview_row_index = row_index 

        self.update_geometry()

    def update_geometry(self):
        zoom = self.parent_view.zoom_level
        t_height = self.parent_view.track_height 
        
        x_pos = TRACK_HEADER_WIDTH + (self.current_start_time * zoom)
        width = self.duration * zoom
        
        target_row = self._preview_row_index if self._is_dragging else self.row_index
        y_pos = HEADER_HEIGHT + (target_row * t_height) + 1
        height = t_height - 2 

        self.setRect(0, 0, width, height)
        self.setPos(x_pos, y_pos)
        self.setZValue(10 if self.isSelected() else 1)

        if t_height < 20:
            self.text.setVisible(False)
        else:
            self.text.setVisible(True)
            self.text.setTextWidth(width - 5)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_start_x = event.scenePos().x()
            self._drag_start_y = event.scenePos().y()
            self._initial_pos_x = self.pos().x()
            self._initial_pos_y = self.pos().y()
            self._preview_row_index = self.row_index
            
            self.setOpacity(0.6) 
            self.setCursor(Qt.ClosedHandCursor)
            self.parent_view.sig_layer_selected.emit(self.layer_id)
            self.setZValue(99) 
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            # 1. Hitung Posisi Waktu (X)
            delta_x = event.scenePos().x() - self._drag_start_x
            raw_new_x = max(TRACK_HEADER_WIDTH, self._initial_pos_x + delta_x)
            
            raw_time = (raw_new_x - TRACK_HEADER_WIDTH) / self.parent_view.zoom_level
            snapped_time = round(raw_time * FPS) / FPS
            
            # 2. Hitung Target Track (Y)
            current_mouse_y = event.scenePos().y()
            th = self.parent_view.track_height
            
            # Estimasi track murni berdasarkan posisi mouse
            estimated_row = int((current_mouse_y - HEADER_HEIGHT) // th)
            estimated_row = max(0, estimated_row)
            
            # Update Preview Row (Hanya visual, belum shift beneran)
            self._preview_row_index = estimated_row
            
            # Auto-Expand Visual jika drag ke bawah
            if estimated_row > self.parent_view._max_visual_row:
                self.parent_view._max_visual_row = estimated_row + 5
                self.parent_view._refresh_layout() 

            snapped_pixel_x = TRACK_HEADER_WIDTH + (snapped_time * self.parent_view.zoom_level)
            final_pixel_y = HEADER_HEIGHT + (estimated_row * th) + 1
            
            self.setPos(snapped_pixel_x, final_pixel_y)
            
            # Tooltip Info: Beritahu user aksi apa yang akan terjadi
            colliding = self.parent_view.check_collision_only(self.layer_id, estimated_row, snapped_time, self.duration)
            action_text = "Insert & Push Down" if colliding else "Move"
            self.setToolTip(f"Start: {self.parent_view.format_time_full(snapped_time)}\nTrack: {estimated_row + 1}\nAction: {action_text}")
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_dragging:
            self._is_dragging = False
            self.setOpacity(0.9 if not self.isSelected() else 1.0)
            self.setCursor(Qt.ArrowCursor)
            self.setZValue(10 if self.isSelected() else 1)
            
            # 1. Hitung Waktu Akhir
            final_pixel_x = self.pos().x()
            new_start_time = (final_pixel_x - TRACK_HEADER_WIDTH) / self.parent_view.zoom_level
            new_start_time = round(new_start_time * FPS) / FPS
            
            # 2. Hitung Track Tujuan
            target_row_index = self._preview_row_index
            
            # 3. 🔥 LOGIKA INSERT & PUSH DOWN 🔥
            # Cek apakah ada clip lain di lokasi target
            is_colliding = self.parent_view.check_collision_only(self.layer_id, target_row_index, new_start_time, self.duration)
            
            if is_colliding:
                # Jika nabrak, geser semua track dari titik ini ke bawah
                self.parent_view.push_tracks_down(from_row=target_row_index, exclude_id=self.layer_id)
            
            # 4. Update Clip yang di-drag
            time_changed = abs(new_start_time - self.current_start_time) > 0.001
            track_changed = target_row_index != self.row_index
            
            if time_changed or track_changed:
                self.row_index = target_row_index
                self.current_start_time = new_start_time
                self.parent_view.sig_request_move.emit(self.layer_id, new_start_time, target_row_index)
            
            self.update_geometry()
            self.parent_view._refresh_layout()
            
        super().mouseReleaseEvent(event)
        
    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemSelectedChange:
            self.setPen(QPen(QColor("#00AEEF"), 2) if value else QPen(QColor("#ffffff"), 1))
            self.setZValue(10 if value else 1)
        return super().itemChange(change, value)


class LayerPanel(QGraphicsView):
    # Signals
    sig_request_seek = Signal(float)       
    sig_layer_selected = Signal(str)       
    sig_request_move = Signal(str, float, int) 
    
    # Binder Signals
    sig_request_add = Signal(str)          
    sig_request_delete = Signal()
    sig_request_reorder = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)

        # State Variables
        self.zoom_level = 50.0  
        self.min_zoom = 1.0     
        self.max_zoom = 600.0   
        self.track_height = 25 
        self.min_track_height = 18
        self.max_track_height = 25
        
        self._is_scrubbing = False 
        self._max_visual_row = 6 
        
        # [BARU] Simpan waktu saat ini untuk sinkronisasi zoom
        self.current_time = 0.0

        self.clip_registry = {}
        self.last_layers_data = [] 

        # Playhead
        self.playhead = QGraphicsLineItem()
        self.playhead.setPen(QPen(QColor("#ff0000"), 1.5))
        self.playhead.setZValue(9999) 
        self.scene.addItem(self.playhead)
        
        self.scene.setSceneRect(0, 0, 2000, 500)

    # ==========================================
    # LOGIKA INSERT & PUSH DOWN (CORE BARU)
    # ==========================================
    def check_collision_only(self, ignore_id, track_idx, start_time, duration):
        """Hanya mengecek apakah ada tabrakan (Return True/False)"""
        end_time = start_time + duration
        for item in self.clip_registry.values():
            if item.layer_id == ignore_id: continue
            
            # Gunakan row_index real (bukan preview)
            if item.row_index != track_idx: continue
            
            item_end = item.current_start_time + item.duration
            if (start_time < item_end) and (end_time > item.current_start_time):
                return True
        return False

    def push_tracks_down(self, from_row, exclude_id):
        """
        Menggeser SEMUA clip yang berada di track >= from_row ke bawah (row + 1).
        Ini menciptakan efek menyisipkan track baru.
        """
        # Kita perlu mengupdate data satu per satu
        # Tips: Update yang row-nya paling besar dulu biar ga numpuk visualnya (opsional)
        
        items_to_move = []
        for item in self.clip_registry.values():
            if item.layer_id == exclude_id: continue
            
            if item.row_index >= from_row:
                items_to_move.append(item)
        
        # Lakukan pergeseran
        for item in items_to_move:
            new_row = item.row_index + 1
            item.row_index = new_row
            
            # Update Visual
            item.update_geometry()
            
            # Update Backend (Emit Signal)
            # Kita asumsikan Controller bisa handle multiple rapid updates
            self.sig_request_move.emit(item.layer_id, item.current_start_time, new_row)

    # ==========================================
    # INPUT HANDLER
    # ==========================================
    def wheelEvent(self, event: QWheelEvent):
        modifiers = event.modifiers()
        delta = event.angleDelta().y()

        if modifiers == Qt.ControlModifier:
            # 1. Zoom Timeline (Anchor Under Mouse)
            factor = 1.05 if delta > 0 else 0.95
            new_zoom = max(self.min_zoom, min(self.zoom_level * factor, self.max_zoom))

            if new_zoom != self.zoom_level:
                # A. Hitung Waktu di Bawah Mouse (Sebelum Zoom)
                # Rumus: SceneX = ViewportX + ScrollX
                #        Time   = (SceneX - HeaderWidth) / OldZoom
                viewport_x = event.position().x()
                scroll_x = self.horizontalScrollBar().value()
                scene_x_old = scroll_x + viewport_x
                
                time_under_mouse = (scene_x_old - TRACK_HEADER_WIDTH) / self.zoom_level

                # B. Terapkan Zoom Baru
                self.zoom_level = new_zoom
                self._refresh_layout()

                # C. Hitung Posisi Scroll Baru (Agar Waktu tsb tetap di posisi mouse)
                # Rumus: NewSceneX = HeaderWidth + (Time * NewZoom)
                #        NewScroll = NewSceneX - ViewportX
                new_scene_x = TRACK_HEADER_WIDTH + (time_under_mouse * self.zoom_level)
                new_scroll_x = int(new_scene_x - viewport_x)

                self.horizontalScrollBar().setValue(new_scroll_x)

            event.accept()

        elif modifiers == Qt.ShiftModifier:
            # Resize Track Height (Logika Lama Tetap Aman)
            step = 5 if delta > 0 else -5
            new_height = max(self.min_track_height, min(self.track_height + step, self.max_track_height))
            if new_height != self.track_height:
                current_v_scroll = self.verticalScrollBar().value()
                self.track_height = new_height
                self._refresh_layout()
                self.verticalScrollBar().setValue(current_v_scroll)
            event.accept()

        else:
            # Standard Scroll (Context Aware: Header vs Track)
            mouse_x = event.position().x()
            if mouse_x < TRACK_HEADER_WIDTH:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta)
            else:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta)
            event.accept()
            
    def _refresh_layout(self):
        for clip in self.clip_registry.values():
            clip.update_geometry()
            
        layer_count = len(self.last_layers_data)
        
        max_duration = 0
        for l in self.last_layers_data:
            end = float(l.properties.get("start_time", 0)) + float(l.properties.get("duration", 0))
            if end > max_duration: max_duration = end

        # Hitung max visual row dari clip yang ada (karena bisa jadi ada di row 50)
        max_visual_row = 0
        for item in self.clip_registry.values():
             # Gunakan row_index atau preview
             r = item._preview_row_index if item._is_dragging else item.row_index
             if r > max_visual_row: max_visual_row = r

        self._max_visual_row = max(self._max_visual_row, max_visual_row)
        total_tracks = self._max_visual_row + 1 # Buffer lebih banyak
        
        # [UBAH BAGIAN AKHIR METHOD INI]
        width = TRACK_HEADER_WIDTH + (max(30.0, max_duration) * self.zoom_level) + 1000 
        height = HEADER_HEIGHT + (total_tracks * self.track_height) + 200
        
        self.scene.setSceneRect(0, 0, width, height)
        self.playhead.setLine(0, HEADER_HEIGHT, 0, height)
        
        # [BARU] Paksa Playhead menempel ke posisi waktu yang benar saat Zoom
        new_playhead_x = TRACK_HEADER_WIDTH + (self.current_time * self.zoom_level)
        self.playhead.setX(new_playhead_x)
        
        self.viewport().update()

    # ==========================================
    # LOGIKA RULER
    # ==========================================
    def get_ruler_settings(self):
        px = self.zoom_level
        if px >= 150:
            if px > 400: return (1.0/FPS * 5, 5, 'frame')
            elif px > 250: return (1.0/FPS * 10, 10, 'frame')
            else: return (0.5, 5, 'frame') 
        elif px >= 40:
            if px >= 80: return (1.0, 10, 'sec')
            else: return (2.0, 4, 'sec')
        elif px >= 10:
             if px >= 20: return (5.0, 5, 'sec') 
             else: return (10.0, 10, 'sec')
        else:
            if px >= 2: return (30.0, 6, 'min')
            elif px >= 0.5: return (60.0, 6, 'min')
            else: return (300.0, 5, 'min')

    def format_time_label(self, seconds, fmt_type):
        is_whole_second = abs(seconds - round(seconds)) < 0.001
        rounded_sec = int(round(seconds))
        mm = int(rounded_sec // 60)
        ss = int(rounded_sec % 60)
        if fmt_type == 'frame':
            if is_whole_second: return f"{mm:02d}:{ss:02d}"
            else:
                frame_num = int(round((seconds - int(seconds)) * FPS))
                return f"{frame_num}f"
        return f"{mm:02d}:{ss:02d}"

    def format_time_full(self, seconds):
        mm = int(seconds // 60)
        ss = int(seconds % 60)
        ff = int((seconds - int(seconds)) * FPS)
        return f"{mm:02d}:{ss:02d}:{ff:02d}"

    # ==========================================
    # RENDERING
    # ==========================================
    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        painter.fillRect(rect, QColor(TRACK_BG_ODD))
        
        top, bottom = int(rect.top()), int(rect.bottom())
        left, right = int(rect.left()), int(rect.right())
        th = self.track_height
        
        first_track_idx = max(0, (top - HEADER_HEIGHT) // th)
        current_y = HEADER_HEIGHT + (first_track_idx * th)
        
        while current_y < bottom:
            idx = (current_y - HEADER_HEIGHT) // th
            if idx % 2 == 0:
                painter.fillRect(QRectF(left, current_y, right - left, th), QColor(TRACK_BG_EVEN))
            painter.setPen(QPen(QColor(GRID_COLOR), 1))
            painter.drawLine(left, current_y, right, current_y)
            current_y += th
            
        major_step, _, _ = self.get_ruler_settings()
        visible_start_x = max(TRACK_HEADER_WIDTH, left)
        start_t = int((visible_start_x - TRACK_HEADER_WIDTH) / self.zoom_level / major_step) * major_step
        
        t = start_t
        while True:
            x = TRACK_HEADER_WIDTH + (t * self.zoom_level)
            if x > right: break
            if x >= TRACK_HEADER_WIDTH:
                painter.setPen(QPen(QColor(GRID_COLOR), 1, Qt.DotLine))
                painter.drawLine(x, max(top, HEADER_HEIGHT), x, bottom)
            t += major_step

    def drawForeground(self, painter: QPainter, rect: QRectF):
        super().drawForeground(painter, rect)
        
        left, top, width = rect.left(), rect.top(), rect.width()
        
        # Ruler
        painter.fillRect(QRectF(left, top, width, HEADER_HEIGHT), QColor(RULER_BG))
        painter.setPen(QPen(QColor("#000"), 1))
        painter.drawLine(left, top + HEADER_HEIGHT, left + width, top + HEADER_HEIGHT)

        # Ticks
        major_step, ticks_per_major, fmt_type = self.get_ruler_settings()
        start_scene_x = max(TRACK_HEADER_WIDTH, left)
        start_idx = int((start_scene_x - TRACK_HEADER_WIDTH) / self.zoom_level / major_step)
        current_t = start_idx * major_step
        end_scene_x = left + width
        
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        fm = painter.fontMetrics()
        
        while True:
            pos_x = TRACK_HEADER_WIDTH + (current_t * self.zoom_level)
            if pos_x > end_scene_x: break
            if pos_x >= TRACK_HEADER_WIDTH:
                painter.setPen(QPen(QColor("#ccc"), 1))
                painter.drawLine(pos_x, top + 18, pos_x, top + HEADER_HEIGHT)
                
                label = self.format_time_label(current_t, fmt_type)
                tw = fm.horizontalAdvance(label)
                label_x = max(TRACK_HEADER_WIDTH + 5, pos_x - tw/2)
                painter.drawText(label_x, top + 13, label)
                
                if ticks_per_major > 1:
                    minor_step_time = major_step / ticks_per_major
                    minor_step_px = minor_step_time * self.zoom_level
                    painter.setPen(QPen(QColor("#666"), 1))
                    for i in range(1, ticks_per_major):
                        sub_x = pos_x + (i * minor_step_px)
                        if sub_x > end_scene_x: break
                        tick_top = top + 24 if i == ticks_per_major/2 else top + 20
                        painter.drawLine(sub_x, tick_top, sub_x, top + HEADER_HEIGHT)
            current_t += major_step

        # Sidebar Header
        painter.fillRect(QRectF(left, top + HEADER_HEIGHT, TRACK_HEADER_WIDTH, rect.height()), QColor(SIDEBAR_BG))
        painter.setPen(QPen(QColor("#000"), 1))
        painter.drawLine(left + TRACK_HEADER_WIDTH, top, left + TRACK_HEADER_WIDTH, rect.bottom())
        
        # Track Names
        first_track_idx = max(0, (int(top) - HEADER_HEIGHT) // self.track_height)
        count = int(rect.height() // self.track_height) + 2
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QColor("#ccc"))
        for i in range(first_track_idx, first_track_idx + count):
            ty = HEADER_HEIGHT + (i * self.track_height)
            painter.drawText(left + 10, ty + self.track_height/2 + 5, f"Track {i+1}")
            painter.setPen(QPen(QColor("#111"), 1))
            painter.drawLine(left, ty + self.track_height, left + TRACK_HEADER_WIDTH, ty + self.track_height)
            painter.setPen(QColor("#ccc"))

        # Corner Box
        painter.fillRect(QRectF(left, top, TRACK_HEADER_WIDTH, HEADER_HEIGHT), QColor("#181818"))
        painter.setPen(QColor("#666"))
        painter.drawText(QRectF(left, top, TRACK_HEADER_WIDTH, HEADER_HEIGHT), Qt.AlignCenter, "TIMELINE")
        painter.setPen(QPen(QColor("#333"), 1))
        painter.drawRect(QRectF(left, top, TRACK_HEADER_WIDTH, HEADER_HEIGHT))

    # ==========================================
    # HELPERS
    # ==========================================
    def sync_all_layers(self, layers: list):
        self.last_layers_data = layers
        for item in self.clip_registry.values():
            self.scene.removeItem(item)
        self.clip_registry.clear()
        
        for i, layer_data in enumerate(layers):
            track_idx = layer_data.properties.get("track_index", i)
            clip = TimelineClipItem(layer_data, track_idx, self)
            self.scene.addItem(clip)
            self.clip_registry[layer_data.id] = clip
        self._refresh_layout()

    def update_playhead(self, t: float):
        self.current_time = t  # [BARU] Update state waktu
        
        x = TRACK_HEADER_WIDTH + (t * self.zoom_level)
        self.playhead.setX(x)
        vis = self.mapToScene(self.viewport().rect()).boundingRect()
        if x > vis.right() - 50:
             self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + 50)

    def _process_seek_event(self, scene_x):
        raw_t = max(0, (scene_x - TRACK_HEADER_WIDTH) / self.zoom_level)
        snapped_t = round(raw_t * FPS) / FPS
        self.sig_request_seek.emit(snapped_t)
        self.update_playhead(snapped_t)

    def mousePressEvent(self, event):
        sp = self.mapToScene(event.pos())
        top_vis = self.mapToScene(0, 0).y()
        if sp.y() < (top_vis + HEADER_HEIGHT) and sp.x() > TRACK_HEADER_WIDTH:
            self._is_scrubbing = True 
            self._process_seek_event(sp.x())
            event.accept() 
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_scrubbing:
            sp = self.mapToScene(event.pos())
            safe_x = max(TRACK_HEADER_WIDTH, sp.x())
            self._process_seek_event(safe_x)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_scrubbing:
            self._is_scrubbing = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def add_item_visual(self, *args): pass
    def remove_item_visual(self, *args): pass
    def clear_visual(self): pass
    def select_item_visual(self, layer_id):
        self.scene.clearSelection()
        if layer_id in self.clip_registry:
            self.clip_registry[layer_id].setSelected(True)