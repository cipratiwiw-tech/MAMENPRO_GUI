# canvas/video_item.py
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import QRectF

class VideoItem(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self._pixmap: QPixmap | None = None
        self._rect = QRectF()
        self.start_time = 0.0
        self.end_time = float("inf")

    def set_pixmap(self, pixmap: QPixmap):
        self.prepareGeometryChange()
        self._pixmap = pixmap
        self._rect = QRectF(pixmap.rect())

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(self, painter: QPainter, option, widget=None):
        if self._pixmap:
            painter.drawPixmap(0, 0, self._pixmap)

    def is_active(self, t: float) -> bool:
        return self.start_time <= t <= self.end_time
