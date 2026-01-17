# gui/center_panel/canvas_items/transform_gizmo.py
import math
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem
from PySide6.QtCore import Qt, QRectF, QPointF, QLineF
from PySide6.QtGui import (
    QPen, QColor, QBrush, QPainterPath, QCursor, 
    QPixmap, QPainter, QPolygonF, QTransform
)

# --- KONFIGURASI VISUAL ---
HANDLE_SIZE = 14          
TOUCH_SIZE = 40           
COLOR_ACCENT = "#00FFFF"  
COLOR_FILL = "#FFFFFF"    
BORDER_WIDTH = 2          

# --- HELPER: GENERATE ROTATED CURSOR ---
class CursorGenerator:
    """Membuat Kursor Panah Resize yang bisa diputar"""
    
    @staticmethod
    def create_resize_cursor(angle_degrees):
        size = 32
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Pindahkan origin ke tengah agar rotasi porosnya benar
        painter.translate(size/2, size/2)
        painter.rotate(angle_degrees)
        
        # Gambar Panah Resize (Garis dengan 2 Kepala)
        # Koordinat relatif terhadap pusat (0,0)
        arrow_len = 10
        head_size = 4
        
        # Outline Hitam (Biar kontras)
        pen_out = QPen(QColor("black"), 3)
        painter.setPen(pen_out)
        painter.drawLine(0, -arrow_len, 0, arrow_len)
        
        # Garis Utama Putih
        pen_in = QPen(QColor("white"), 1.5)
        painter.setPen(pen_in)
        painter.drawLine(0, -arrow_len, 0, arrow_len)
        
        # Gambar Kepala Panah Atas & Bawah
        for direction in [-1, 1]:
            # Polygon Segitiga
            y_tip = arrow_len * direction
            y_base = (arrow_len - head_size) * direction
            
            head = QPolygonF([
                QPointF(0, y_tip),
                QPointF(-head_size, y_base),
                QPointF(head_size, y_base)
            ])
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("black"))
            # Gambar outline kepala sedikit lebih besar
            painter.drawPolygon(head.translated(0, 1 if direction==1 else -1)) # Offset dikit
            
            painter.setBrush(QColor("white"))
            painter.drawPolygon(head)
            
        painter.end()
        
        return QCursor(pix, 16, 16)

    @staticmethod
    def create_rotate_cursor():
        # Kursor Rotasi (Panah Melengkung) - Sama seperti sebelumnya
        size = 32
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen_outline = QPen(QColor("black"), 4)
        painter.setPen(pen_outline)
        painter.drawArc(6, 6, 20, 20, 45 * 16, 270 * 16)
        
        pen_main = QPen(QColor("white"), 2)
        painter.setPen(pen_main)
        painter.drawArc(6, 6, 20, 20, 45 * 16, 270 * 16)
        
        arrow_head = QPolygonF([QPointF(24, 10), QPointF(18, 4), QPointF(20, 14)])
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("black"))
        scale_poly = QPolygonF([QPointF(p.x()+1, p.y()+1) for p in arrow_head])
        painter.drawPolygon(scale_poly)
        
        painter.setBrush(QColor("white"))
        painter.drawPolygon(arrow_head)
        painter.end()
        
        return QCursor(pix, 16, 16)

# --- CLASSES HANDLE ---

class CornerHandle(QGraphicsEllipseItem):
    """Handle Sudut: Bulat Besar"""
    def __init__(self, parent=None):
        super().__init__(-HANDLE_SIZE/2, -HANDLE_SIZE/2, HANDLE_SIZE, HANDLE_SIZE, parent)
        self.setBrush(QBrush(QColor(COLOR_FILL)))
        self.setPen(QPen(QColor(COLOR_ACCENT), BORDER_WIDTH))
        self.setAcceptHoverEvents(True) 
        # Base Angle: Sudut normal handle ini (misal TL = -45 derajat / diagonal kiri)
        self.base_angle = 0 

    def update_cursor(self, parent_rotation):
        """Update cursor berdasarkan rotasi video"""
        final_angle = self.base_angle + parent_rotation
        self.setCursor(CursorGenerator.create_resize_cursor(final_angle))

    def shape(self):
        path = QPainterPath()
        rect = self.rect()
        margin = (TOUCH_SIZE - HANDLE_SIZE) / 2
        path.addEllipse(rect.adjusted(-margin, -margin, margin, margin))
        return path
    
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(COLOR_ACCENT)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(COLOR_FILL)))
        super().hoverLeaveEvent(event)

class SideHandle(QGraphicsRectItem):
    """Handle Sisi: Batang"""
    def __init__(self, vertical=False, parent=None):
        if vertical:
            w, h = HANDLE_SIZE / 2, HANDLE_SIZE
        else:
            w, h = HANDLE_SIZE, HANDLE_SIZE / 2
        super().__init__(-w/2, -h/2, w, h, parent)
        self.setBrush(QBrush(QColor(COLOR_FILL)))
        self.setPen(QPen(QColor(COLOR_ACCENT), BORDER_WIDTH))
        self.setAcceptHoverEvents(True)
        self.base_angle = 0

    def update_cursor(self, parent_rotation):
        final_angle = self.base_angle + parent_rotation
        self.setCursor(CursorGenerator.create_resize_cursor(final_angle))

    def shape(self):
        path = QPainterPath()
        rect = self.rect()
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
    """Handle Rotasi"""
    def __init__(self, parent=None):
        size = HANDLE_SIZE
        super().__init__(-size/2, -size/2, size, size, parent)
        self.setBrush(QBrush(QColor(COLOR_FILL)))
        self.setPen(QPen(QColor("#FF0000"), BORDER_WIDTH)) 
        self.setAcceptHoverEvents(True)
        # Kursor Rotasi tetap sama (tidak perlu diputar)
        self.setCursor(CursorGenerator.create_rotate_cursor())

    def shape(self):
        path = QPainterPath()
        rect = self.rect()
        margin = (TOUCH_SIZE - HANDLE_SIZE) / 2
        path.addEllipse(rect.adjusted(-margin, -margin, margin, margin))
        return path

# --- GIZMO UTAMA ---

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
        
        # --- INIT HANDLES ---
        
        # 1. Corners
        self.tl = CornerHandle(self); self.tl.base_angle = -45 # NW
        self.tr = CornerHandle(self); self.tr.base_angle = 45  # NE
        self.bl = CornerHandle(self); self.bl.base_angle = 45  # SW (Sama kayak NE arrow-nya)
        self.br = CornerHandle(self); self.br.base_angle = -45 # SE
        
        # 2. Sides
        self.t = SideHandle(vertical=False, parent=self); self.t.base_angle = 0   # Vertical Arrow (relative 0 rot) -> Wait, T is vertical move? No T is Height resize
        # Koreksi Base Angle agar panah sesuai arah gerak handle:
        # Top Handle gerak Vertikal -> Arrow Vertikal (0 deg di sistem Qt koordinat painter? atau 90?)
        # Painter drawLine(0, -10, 0, 10) adalah Vertikal (0 derajat).
        # Jadi Top Handle base = 0.
        
        self.b = SideHandle(vertical=False, parent=self); self.b.base_angle = 0
        self.l = SideHandle(vertical=True, parent=self);  self.l.base_angle = 90 # Horizontal Arrow
        self.r = SideHandle(vertical=True, parent=self);  self.r.base_angle = 90
        
        # 3. Rotate
        self.rot_stick = QGraphicsRectItem(0, 0, 2, 30, self) 
        self.rot_stick.setBrush(QBrush(QColor(COLOR_ACCENT)))
        self.rot_stick.setPen(Qt.NoPen)
        self.rot = RotateHandle(self)

        # List semua handle resize untuk update massal
        self.resize_handles = [self.tl, self.tr, self.bl, self.br, self.t, self.b, self.l, self.r]

        self._update_layout()
        self._refresh_cursors() # Set cursor awal

    def boundingRect(self):
        rect = self.parent_item.boundingRect()
        return rect.adjusted(-50, -60, 50, 50)

    def paint(self, painter, option, widget):
        rect = self.parent_item.boundingRect()
        pen = QPen(QColor(COLOR_ACCENT), 2.5) 
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

    def _refresh_cursors(self):
        """Update sudut kursor semua handle sesuai rotasi item saat ini"""
        current_rot = self.parent_item.rotation()
        for handle in self.resize_handles:
            handle.update_cursor(current_rot)

    # --- EVENT HANDLERS ---
    
    def sceneEventFilter(self, watched, event):
        return super().sceneEventFilter(watched, event)

    def mousePressEvent(self, event):
        sp = event.scenePos()
        def is_hit(item): return item.contains(item.mapFromScene(sp))

        if is_hit(self.rot):
            self._mode = 'ROTATE'
        elif any(is_hit(h) for h in [self.br, self.tr, self.bl, self.tl, self.r, self.l, self.t, self.b]):
            self._mode = 'SCALE'
        else:
            event.ignore(); return

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
            # Hitung sudut
            angle = math.degrees(math.atan2(dy, dx)) + 90
            
            # Snap Shift
            if event.modifiers() == Qt.ShiftModifier:
                angle = round(angle / 45) * 45
            
            self.parent_item.setRotation(angle)
            
            # 🔥 LIVE UPDATE CURSOR SAAT ROTASI 🔥
            self._refresh_cursors()

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