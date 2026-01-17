# gui/center_panel/canvas_items/transform_gizmo.py
import math
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath, QCursor

# --- KONFIGURASI VISUAL "MENONJOL" ---
HANDLE_SIZE = 14          # Ukuran visual (lebih besar dari sebelumnya 10)
TOUCH_SIZE = 40           # Area deteksi mouse (sangat luas agar gampang diklik)
COLOR_ACCENT = "#00FFFF"  # Cyan Terang (Border)
COLOR_FILL = "#FFFFFF"    # Putih Solid (Isi)
BORDER_WIDTH = 2          # Ketebalan garis handle

class CornerHandle(QGraphicsEllipseItem):
    """Handle Sudut: Bulat Besar (Resize Uniform)"""
    def __init__(self, cursor, parent=None):
        # Visual: Lingkaran
        super().__init__(-HANDLE_SIZE/2, -HANDLE_SIZE/2, HANDLE_SIZE, HANDLE_SIZE, parent)
        
        # Style High Contrast
        self.setBrush(QBrush(QColor(COLOR_FILL)))
        self.setPen(QPen(QColor(COLOR_ACCENT), BORDER_WIDTH))
        
        self.setCursor(cursor)
        self.setAcceptHoverEvents(True) 

    def shape(self):
        """Hitbox luas"""
        path = QPainterPath()
        rect = self.rect()
        margin = (TOUCH_SIZE - HANDLE_SIZE) / 2
        path.addEllipse(rect.adjusted(-margin, -margin, margin, margin))
        return path
    
    # Efek Hover (Opsional: Berubah warna saat mouse di atasnya)
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(COLOR_ACCENT))) # Jadi Cyan saat hover
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(COLOR_FILL))) # Kembali Putih
        super().hoverLeaveEvent(event)

class SideHandle(QGraphicsRectItem):
    """Handle Sisi: Kotak/Batang (Resize/Crop Stretch)"""
    def __init__(self, cursor, vertical=False, parent=None):
        # Visual: Persegi Panjang (Pil)
        if vertical:
            w, h = HANDLE_SIZE / 2, HANDLE_SIZE
        else:
            w, h = HANDLE_SIZE, HANDLE_SIZE / 2
            
        super().__init__(-w/2, -h/2, w, h, parent)
        
        self.setBrush(QBrush(QColor(COLOR_FILL)))
        self.setPen(QPen(QColor(COLOR_ACCENT), BORDER_WIDTH))
        self.setCursor(cursor)
        self.setAcceptHoverEvents(True)

    def shape(self):
        path = QPainterPath()
        rect = self.rect()
        # Hitbox tetap kotak besar meski visualnya pipih
        size = max(rect.width(), rect.height())
        diff_x = (TOUCH_SIZE - rect.width()) / 2
        diff_y = (TOUCH_SIZE - rect.height()) / 2
        path.addRect(rect.adjusted(-diff_x, -diff_y, diff_x, diff_y))
        return path
        
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(COLOR_ACCENT)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(COLOR_FILL)))
        super().hoverLeaveEvent(event)

class RotateHandle(QGraphicsEllipseItem):
    """Handle Rotasi: Lingkaran di atas"""
    def __init__(self, parent=None):
        size = HANDLE_SIZE
        super().__init__(-size/2, -size/2, size, size, parent)
        
        self.setBrush(QBrush(QColor(COLOR_FILL)))
        self.setPen(QPen(QColor("#FF0000"), BORDER_WIDTH)) # Merah untuk Rotasi (Pembeda)
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptHoverEvents(True)

    def shape(self):
        path = QPainterPath()
        rect = self.rect()
        margin = (TOUCH_SIZE - HANDLE_SIZE) / 2
        path.addEllipse(rect.adjusted(-margin, -margin, margin, margin))
        return path

class TransformGizmo(QGraphicsItem):
    def __init__(self, parent_item):
        super().__init__(parent_item)
        self.parent_item = parent_item
        self.setZValue(9999) 
        
        # State
        self._dragging = False
        self._mode = None 
        self._start_pos = None
        self._start_scale = 1.0
        self._start_rotation = 0.0
        self._parent_center = QPointF()
        
        # --- BUAT HANDLES (Bentuk Beda-Beda) ---
        
        # 1. Corners (Lingkaran)
        self.tl = CornerHandle(Qt.SizeFDiagCursor, self) 
        self.tr = CornerHandle(Qt.SizeBDiagCursor, self) 
        self.bl = CornerHandle(Qt.SizeBDiagCursor, self) 
        self.br = CornerHandle(Qt.SizeFDiagCursor, self) 
        
        # 2. Sides (Batang)
        self.t = SideHandle(Qt.SizeVerCursor, vertical=False, parent=self)
        self.b = SideHandle(Qt.SizeVerCursor, vertical=False, parent=self)
        self.l = SideHandle(Qt.SizeHorCursor, vertical=True, parent=self)
        self.r = SideHandle(Qt.SizeHorCursor, vertical=True, parent=self)
        
        # 3. Rotate (Garis + Lingkaran)
        self.rot_stick = QGraphicsRectItem(0, 0, 2, 30, self) 
        self.rot_stick.setBrush(QBrush(QColor(COLOR_ACCENT)))
        self.rot_stick.setPen(Qt.NoPen)
        self.rot = RotateHandle(self)

        self._update_layout()

    def boundingRect(self):
        rect = self.parent_item.boundingRect()
        return rect.adjusted(-50, -60, 50, 50)

    def paint(self, painter, option, widget):
        rect = self.parent_item.boundingRect()
        
        # Gambar Border Seleksi (Garis Putus-putus Tebal)
        pen = QPen(QColor(COLOR_ACCENT), 2.5) # Lebih tebal
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)

    def _update_layout(self):
        rect = self.parent_item.boundingRect()
        
        # Posisi Sudut
        self.tl.setPos(rect.topLeft())
        self.tr.setPos(rect.topRight())
        self.bl.setPos(rect.bottomLeft())
        self.br.setPos(rect.bottomRight())
        
        # Posisi Sisi
        self.t.setPos(rect.center().x(), rect.top())
        self.b.setPos(rect.center().x(), rect.bottom())
        self.l.setPos(rect.left(), rect.center().y())
        self.r.setPos(rect.right(), rect.center().y())
        
        # Posisi Rotasi
        rot_dist = 30
        self.rot.setPos(rect.center().x(), rect.top() - rot_dist)
        self.rot_stick.setRect(rect.center().x() - 1, rect.top() - rot_dist, 2, rot_dist)

    # --- EVENT LOGIC (Sama seperti sebelumnya, tapi diperkuat) ---
    
    def sceneEventFilter(self, watched, event):
        return super().sceneEventFilter(watched, event)

    def mousePressEvent(self, event):
        sp = event.scenePos()
        
        # Helper Hit Test
        def is_hit(item):
            return item.contains(item.mapFromScene(sp))

        if is_hit(self.rot):
            self._mode = 'ROTATE'
        
        elif is_hit(self.br) or is_hit(self.tr) or is_hit(self.bl) or is_hit(self.tl):
            self._mode = 'SCALE' # Uniform Scale
        
        elif is_hit(self.r) or is_hit(self.l) or is_hit(self.t) or is_hit(self.b):
            self._mode = 'SCALE' # Sementara masih Uniform (bisa diubah jadi stretch/crop nanti)
        
        else:
            event.ignore()
            return

        self._dragging = True
        self._start_pos = event.scenePos()
        self._start_scale = self.parent_item.scale()
        self._start_rotation = self.parent_item.rotation()
        self._parent_center = self.parent_item.sceneBoundingRect().center()
        
        event.accept()

    def mouseMoveEvent(self, event):
        if not self._dragging: return

        curr_pos = event.scenePos()
        cx, cy = self._parent_center.x(), self._parent_center.y()

        if self._mode == 'ROTATE':
            dx = curr_pos.x() - cx
            dy = curr_pos.y() - cy
            angle = math.degrees(math.atan2(dy, dx)) + 90
            if event.modifiers() == Qt.ShiftModifier:
                angle = round(angle / 45) * 45
            self.parent_item.setRotation(angle)

        elif self._mode == 'SCALE':
            start_dist = math.hypot(self._start_pos.x() - cx, self._start_pos.y() - cy)
            curr_dist = math.hypot(curr_pos.x() - cx, curr_pos.y() - cy)
            
            if start_dist < 1: return
            
            ratio = curr_dist / start_dist
            new_scale = self._start_scale * ratio
            if new_scale < 0.1: new_scale = 0.1
            
            self.parent_item.setScale(new_scale)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self._mode = None
            
            if hasattr(self.parent_item, "notify_transform_change"):
                self.parent_item.notify_transform_change()
            
            event.accept()
        else:
            super().mouseReleaseEvent(event)