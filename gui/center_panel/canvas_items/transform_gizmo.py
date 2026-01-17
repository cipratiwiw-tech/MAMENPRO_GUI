# gui/center_panel/canvas_items/transform_gizmo.py
import math
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem
from PySide6.QtCore import Qt, QRectF, QPointF, QEvent
from PySide6.QtGui import (
    QPen, QColor, QBrush, QPainterPath, QCursor, 
    QPixmap, QPainter, QPolygonF
)

# --- KONFIGURASI VISUAL ---
HANDLE_SIZE = 16           
ROTATE_HANDLE_SIZE = 22    
TOUCH_SIZE = 60            # Area Hitbox (Cukup besar tapi tidak overlapping parah)
COLOR_ACCENT = "#00FFFF"   
COLOR_FILL = "#FFFFFF"     
BORDER_WIDTH = 2.5         

# --- CURSOR GENERATOR (Visual Panah) ---
class CursorGenerator:
    @staticmethod
    def create_resize_cursor(angle_degrees):
        size = 32
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(size/2, size/2)
        painter.rotate(angle_degrees)
        
        arrow_len = 10
        head_size = 5
        
        pen_out = QPen(QColor("black"), 4)
        painter.setPen(pen_out)
        painter.drawLine(0, -arrow_len, 0, arrow_len)
        
        pen_in = QPen(QColor("white"), 2)
        painter.setPen(pen_in)
        painter.drawLine(0, -arrow_len, 0, arrow_len)
        
        for direction in [-1, 1]:
            y_tip = arrow_len * direction
            y_base = (arrow_len - head_size) * direction
            head = QPolygonF([QPointF(0, y_tip), QPointF(-head_size, y_base), QPointF(head_size, y_base)])
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("black"))
            painter.drawPolygon(head.translated(0, 1 if direction==1 else -1))
            painter.setBrush(QColor("white"))
            painter.drawPolygon(head)
        painter.end()
        return QCursor(pix, 16, 16)

    @staticmethod
    def create_rotate_cursor():
        size = 32
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen_outline = QPen(QColor("black"), 5)
        painter.setPen(pen_outline)
        painter.drawArc(6, 6, 20, 20, 45 * 16, 270 * 16)
        
        pen_main = QPen(QColor("white"), 2.5)
        painter.setPen(pen_main)
        painter.drawArc(6, 6, 20, 20, 45 * 16, 270 * 16)
        
        arrow_head = QPolygonF([QPointF(24, 10), QPointF(18, 4), QPointF(20, 14)])
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("black"))
        painter.drawPolygon(QPolygonF([QPointF(p.x()+1, p.y()+1) for p in arrow_head]))
        painter.setBrush(QColor("white"))
        painter.drawPolygon(arrow_head)
        painter.end()
        return QCursor(pix, 16, 16)

# --- HANDLE CLASSES (VISUAL ONLY) ---
# Handle sekarang "bodoh", hanya untuk tampilan & hitbox. 
# Logika interaksi dipegang penuh oleh Gizmo via EventFilter.

class CornerHandle(QGraphicsEllipseItem):
    def __init__(self, parent=None):
        super().__init__(-HANDLE_SIZE/2, -HANDLE_SIZE/2, HANDLE_SIZE, HANDLE_SIZE, parent)
        self.setBrush(QBrush(QColor(COLOR_FILL)))
        self.setPen(QPen(QColor(COLOR_ACCENT), BORDER_WIDTH))
        self.setAcceptHoverEvents(True) 
        self.base_angle = 0 

    def update_cursor(self, parent_rotation):
        self.setCursor(CursorGenerator.create_resize_cursor(self.base_angle + parent_rotation))

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
    def __init__(self, vertical=False, parent=None):
        if vertical: w, h = HANDLE_SIZE / 2.5, HANDLE_SIZE
        else: w, h = HANDLE_SIZE, HANDLE_SIZE / 2.5
        super().__init__(-w/2, -h/2, w, h, parent)
        self.setBrush(QBrush(QColor(COLOR_FILL)))
        self.setPen(QPen(QColor(COLOR_ACCENT), BORDER_WIDTH))
        self.setAcceptHoverEvents(True)
        self.base_angle = 0

    def update_cursor(self, parent_rotation):
        self.setCursor(CursorGenerator.create_resize_cursor(self.base_angle + parent_rotation))

    def shape(self):
        path = QPainterPath()
        rect = self.rect()
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
    def __init__(self, parent=None):
        s = ROTATE_HANDLE_SIZE
        super().__init__(-s/2, -s/2, s, s, parent)
        self.setBrush(QBrush(QColor(COLOR_FILL)))
        self.setPen(QPen(QColor("#FF0000"), BORDER_WIDTH)) 
        self.setAcceptHoverEvents(True)
        self.setCursor(CursorGenerator.create_rotate_cursor())

    def shape(self):
        path = QPainterPath()
        rect = self.rect()
        margin = (TOUCH_SIZE - ROTATE_HANDLE_SIZE) / 2
        path.addEllipse(rect.adjusted(-margin, -margin, margin, margin))
        return path
    
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor("#FF0000"))) 
        super().hoverEnterEvent(event)
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(COLOR_FILL)))
        super().hoverLeaveEvent(event)

# --- MAIN GIZMO (SATU PINTU LOGIKA) ---

class TransformGizmo(QGraphicsItem):
    def __init__(self, parent_item):
        super().__init__(parent_item)
        self.parent_item = parent_item
        self.setZValue(9999) 
        
        # State Dragging
        self._dragging = False
        self._mode = None 
        self._active_handle = None # Handle yang sedang ditarik
        
        self._start_pos = None
        self._start_scale = 1.0
        self._start_rotation = 0.0
        self._parent_center = QPointF()
        
        # --- INIT HANDLES ---
        self.tl = CornerHandle(self); self.tl.base_angle = -45
        self.tr = CornerHandle(self); self.tr.base_angle = 45
        self.bl = CornerHandle(self); self.bl.base_angle = 45
        self.br = CornerHandle(self); self.br.base_angle = -45
        
        self.t = SideHandle(vertical=False, parent=self); self.t.base_angle = 0
        self.b = SideHandle(vertical=False, parent=self); self.b.base_angle = 0
        self.l = SideHandle(vertical=True, parent=self);  self.l.base_angle = 90
        self.r = SideHandle(vertical=True, parent=self);  self.r.base_angle = 90
        
        self.rot_stick = QGraphicsRectItem(0, 0, 3, 40, self) 
        self.rot_stick.setBrush(QBrush(QColor(COLOR_ACCENT)))
        self.rot_stick.setPen(Qt.NoPen)
        self.rot = RotateHandle(self)

        self.all_handles = [self.tl, self.tr, self.bl, self.br, self.t, self.b, self.l, self.r, self.rot]
        self.resize_handles = [self.tl, self.tr, self.bl, self.br, self.t, self.b, self.l, self.r]

        self._update_layout()
        self._refresh_cursors()

        # 🔥 FILTER EVENT: Gizmo akan "mencegat" semua event mouse pada handle 🔥
        # Ini mencegah event tembus ke VideoItem di bawahnya.
        for handle in self.all_handles:
            handle.installSceneEventFilter(self)

    def boundingRect(self):
        # Bounding rect Gizmo tidak perlu besar, karena interaksi ditangani per handle
        return self.parent_item.boundingRect()

    def paint(self, painter, option, widget):
        rect = self.parent_item.boundingRect()
        pen = QPen(QColor(COLOR_ACCENT), 2.5) 
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)

    def _update_layout(self):
        rect = self.parent_item.boundingRect()
        self.tl.setPos(rect.topLeft())
        self.tr.setPos(rect.topRight())
        self.bl.setPos(rect.bottomLeft())
        self.br.setPos(rect.bottomRight())
        self.t.setPos(rect.center().x(), rect.top())
        self.b.setPos(rect.center().x(), rect.bottom())
        self.l.setPos(rect.left(), rect.center().y())
        self.r.setPos(rect.right(), rect.center().y())
        
        rot_dist = 40 
        self.rot.setPos(rect.center().x(), rect.top() - rot_dist)
        self.rot_stick.setRect(rect.center().x() - 1.5, rect.top() - rot_dist, 3, rot_dist)

    def _refresh_cursors(self):
        current_rot = self.parent_item.rotation()
        for handle in self.resize_handles:
            handle.update_cursor(current_rot)
    def refresh(self):
        """
        Dipanggil saat parent berubah:
        - pixmap berubah
        - scale / rotate
        - origin update
        """
        self.prepareGeometryChange()
        self._update_layout()
        self._refresh_cursors()
        self.update()


    # --- 🔥 SCENE EVENT FILTER (JANTUNG UTAMA) 🔥 ---
    # Fungsi ini akan dipanggil SETIAP KALI ada mouse event pada salah satu handle.
    
    def sceneEventFilter(self, watched, event):
        # Apakah yang diklik adalah salah satu handle kita?
        if watched not in self.all_handles:
            return super().sceneEventFilter(watched, event)

        # 1. MOUSE PRESS (Mulai Drag)
        if event.type() == QEvent.GraphicsSceneMousePress:
            if event.button() == Qt.LeftButton:
                self._dragging = True
                self._active_handle = watched
                self._start_pos = event.scenePos()
                self._start_scale = self.parent_item.scale()
                self._start_rotation = self.parent_item.rotation()
                self._parent_center = self.parent_item.sceneBoundingRect().center()
                
                # Tentukan Mode
                if watched == self.rot:
                    self._mode = 'ROTATE'
                else:
                    self._mode = 'SCALE'
                
                # PENTING: Return True agar event STOP di sini.
                # VideoItem tidak akan pernah tahu kalau handle diklik.
                return True 

        # 2. MOUSE MOVE (Proses Drag)
        elif event.type() == QEvent.GraphicsSceneMouseMove:
            if self._dragging and self._active_handle == watched:
                self._handle_drag(event.scenePos(), event.modifiers())
                return True # Stop propagation

        # 3. MOUSE RELEASE (Selesai)
        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            if self._dragging and self._active_handle == watched:
                self._dragging = False
                self._mode = None
                self._active_handle = None
                
                # Simpan perubahan
                if hasattr(self.parent_item, "notify_transform_change"):
                    self.parent_item.notify_transform_change()
                
                return True # Stop propagation

        return super().sceneEventFilter(watched, event)

    def _handle_drag(self, curr_pos, modifiers):
        cx, cy = self._parent_center.x(), self._parent_center.y()

        if self._mode == 'ROTATE':
            dx = curr_pos.x() - cx
            dy = curr_pos.y() - cy
            angle = math.degrees(math.atan2(dy, dx)) + 90
            
            if modifiers == Qt.ShiftModifier:
                angle = round(angle / 45) * 45
            
            self.parent_item.setRotation(angle)
            self._refresh_cursors() 
            self.refresh()

        elif self._mode == 'SCALE':
            start_dist = math.hypot(self._start_pos.x() - cx, self._start_pos.y() - cy)
            curr_dist = math.hypot(curr_pos.x() - cx, curr_pos.y() - cy)
            
            if start_dist < 1: return
            
            # Logic Uniform Scale sederhana
            # Bisa dikembangkan jadi stretch X/Y tergantung handle jika mau
            ratio = curr_dist / start_dist
            new_scale = self._start_scale * ratio
            
            if new_scale < 0.1: new_scale = 0.1
            self.parent_item.setScale(new_scale)
            self.refresh()