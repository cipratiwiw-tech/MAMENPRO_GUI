from PySide6.QtWidgets import QGraphicsView, QFrame, QGraphicsRectItem, QGraphicsPathItem
from PySide6.QtGui import QPainter, QMouseEvent, QWheelEvent, QBrush, QColor, QPen, QPainterPath
from PySide6.QtCore import Qt

# Import hanya untuk pengecekan tipe (agar View tau mana yang VideoItem)
from gui.center_panel.video_item import VideoItem 

class CanvasContainer(QGraphicsRectItem):
    def __init__(self, w, h):
        super().__init__(0, 0, w, h)
        self.setBrush(QBrush(QColor("#1e1e1e")))
        self.setPen(QPen(QColor("#333333"), 1))
        self.setZValue(0)

class DimmingOverlay(QGraphicsPathItem):
    def __init__(self, canvas_rect):
        super().__init__()
        self.setBrush(QBrush(QColor(0, 0, 0, 180)))
        self.setPen(Qt.NoPen)
        self.setZValue(10)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.update_mask(canvas_rect)

    def update_mask(self, canvas_rect):
        path = QPainterPath()
        path.addRect(-50000, -50000, 100000, 100000) # Area infinite gelap
        path.addRect(canvas_rect) # Area terang (lubang)
        self.setPath(path)

class VideoGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setAlignment(Qt.AlignCenter)
        self.setBackgroundBrush(QBrush(QColor("#0a0a0a")))
        self.setFrameShape(QFrame.NoFrame)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate) 

    def wheelEvent(self, event: QWheelEvent):
        # Zoom Logic
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event: QMouseEvent):
        # Pan Logic (Spasi/Ctrl + Click)
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            # Fake event agar View langsung merespon drag
            fake = QMouseEvent(event.type(), event.position(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
            super().mousePressEvent(fake)
            return

        # Selection Logic
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.position().toPoint())
            item = self.scene().itemAt(pos, self.transform())
            
            # Jika klik VideoItem -> Mode Select biasa
            if isinstance(item, VideoItem): 
                self.setDragMode(QGraphicsView.NoDrag)
            # Jika klik background -> Mode RubberBand (kotak seleksi biru)
            else:
                self.setDragMode(QGraphicsView.RubberBandDrag)
                
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        self.setDragMode(QGraphicsView.NoDrag)