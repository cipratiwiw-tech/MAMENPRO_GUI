# gui/center_panel/canvas_items/transform_gizmo.py
import math
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QBrush, QCursor

class HandleItem(QGraphicsRectItem):
    """Kotak kecil (Handle) untuk Resize"""
    def __init__(self, cursor_type, parent=None):
        super().__init__(-6, -6, 12, 12, parent)
        self.setBrush(QBrush(QColor("white")))
        self.setPen(QPen(QColor("black"), 1))
        self.setCursor(cursor_type)
        # Agar handle tidak ikut gepeng saat parent di-scale (Inverse Scale logic bisa ditambahkan nanti)
        # Untuk stabilitas v1, kita biarkan ikut scale.

class RotateHandle(QGraphicsEllipseItem):
    """Lingkaran di atas untuk Rotasi"""
    def __init__(self, parent=None):
        super().__init__(-7, -7, 14, 14, parent)
        self.setBrush(QBrush(QColor("#00FFFF"))) # Cyan
        self.setPen(QPen(QColor("black"), 1))
        self.setCursor(Qt.PointingHandCursor)

class TransformGizmo(QGraphicsItem):
    def __init__(self, parent_item):
        super().__init__(parent_item)
        self.parent_item = parent_item
        self.setZValue(9999) # Selalu di atas
        
        # State
        self._dragging = False
        self._mode = None # 'ROTATE' atau 'SCALE'
        self._start_pos = None
        self._start_scale = 1.0
        self._start_rotation = 0.0
        
        # Visual Bounds (Garis Putus-putus)
        self.border_rect = QRectF()
        
        # Buat Handles
        self.tl = HandleItem(Qt.SizeFDiagCursor, self) # Top Left
        self.tr = HandleItem(Qt.SizeBDiagCursor, self) # Top Right
        self.bl = HandleItem(Qt.SizeBDiagCursor, self) # Bottom Left
        self.br = HandleItem(Qt.SizeFDiagCursor, self) # Bottom Right
        
        # Rotate Handle
        self.rot = RotateHandle(self)
        
        # Update posisi handle
        self._update_layout()

    def boundingRect(self):
        # Area bounding box + sedikit padding untuk handles
        rect = self.parent_item.boundingRect()
        return rect.adjusted(-20, -30, 20, 20)

    def paint(self, painter, option, widget):
        # Gambar Garis Batas Biru Putus-putus
        rect = self.parent_item.boundingRect()
        
        pen = QPen(QColor("#00AEEF"), 2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)
        
        # Gambar Garis ke Rotate Handle
        painter.drawLine(int(rect.center().x()), int(rect.top()), 
                         int(self.rot.x()), int(self.rot.y()))

    def _update_layout(self):
        """Posisikan handle sesuai ukuran parent"""
        rect = self.parent_item.boundingRect()
        
        self.tl.setPos(rect.topLeft())
        self.tr.setPos(rect.topRight())
        self.bl.setPos(rect.bottomLeft())
        self.br.setPos(rect.bottomRight())
        
        # Rotate handle di tengah atas, sedikit keluar
        self.rot.setPos(rect.center().x(), rect.top() - 30)

    # --- INTERAKSI ---
    
    def sceneEventFilter(self, watched, event):
        # Kita menangani event dari child items (handles) di sini
        return super().sceneEventFilter(watched, event)

    def mousePressEvent(self, event):
        # Deteksi bagian mana yang diklik
        sp = event.scenePos()
        item = self.scene().itemAt(sp, self.scene().views()[0].transform())
        
        if item == self.rot:
            self._mode = 'ROTATE'
        elif item in [self.tl, self.tr, self.bl, self.br]:
            self._mode = 'SCALE'
            self._ref_handle = item # Simpan handle mana yang ditarik
        else:
            event.ignore() # Biarkan tembus ke parent untuk drag move biasa
            return

        self._dragging = True
        self._start_pos = event.scenePos()
        self._start_scale = self.parent_item.scale()
        self._start_rotation = self.parent_item.rotation()
        self._parent_center = self.parent_item.sceneBoundingRect().center()
        
        event.accept()

    def mouseMoveEvent(self, event):
        if not self._dragging: return

        current_pos = event.scenePos()

        if self._mode == 'ROTATE':
            # Hitung sudut baru relative terhadap center item
            dx = current_pos.x() - self._parent_center.x()
            dy = current_pos.y() - self._parent_center.y()
            angle = math.degrees(math.atan2(dy, dx)) + 90 # +90 karena 0 derajat itu arah jam 3
            
            # Snap 45 derajat jika Shift ditekan
            if event.modifiers() == Qt.ShiftModifier:
                angle = round(angle / 45) * 45
                
            self.parent_item.setRotation(angle)

        elif self._mode == 'SCALE':
            # Hitung jarak dari center ke mouse saat ini vs saat mulai
            # Ini adalah Uniform Scale (Aspect Ratio terjaga)
            
            # Jarak awal
            start_dist = math.hypot(
                self._start_pos.x() - self._parent_center.x(),
                self._start_pos.y() - self._parent_center.y()
            )
            
            # Jarak sekarang
            curr_dist = math.hypot(
                current_pos.x() - self._parent_center.x(),
                current_pos.y() - self._parent_center.y()
            )
            
            if start_dist == 0: return 
            
            scale_factor = curr_dist / start_dist
            new_scale = self._start_scale * scale_factor
            
            # Batasi minimum scale agar tidak error/hilang
            if new_scale < 0.1: new_scale = 0.1
            
            self.parent_item.setScale(new_scale)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self._mode = None
            
            # 🔥 TRIGGER SIMPAN KE CONTROLLER VIA PARENT 🔥
            # Panggil logic simpan di parent item
            if hasattr(self.parent_item, "notify_transform_change"):
                self.parent_item.notify_transform_change()
            
            event.accept()
        else:
            super().mouseReleaseEvent(event)