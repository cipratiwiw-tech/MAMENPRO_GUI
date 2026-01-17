# canvas/video_item.py

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPainter
from PySide6.QtCore import QRectF

class VideoItem(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self.video_path = None
        self._rect = QRectF(0, 0, 640, 360)  # placeholder size

    def set_video_source(self, video_path: str):
        self.video_path = video_path

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(self, painter: QPainter, option, widget=None):
        # BELUM render video
        # cuma placeholder biar keliatan item masuk scene
        painter.drawRect(self._rect)
