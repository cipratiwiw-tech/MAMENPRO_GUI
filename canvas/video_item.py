# canvas/video_item.py
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtGui import QPixmap, QColor, QPen
from PySide6.QtCore import Qt

class VideoItem(QGraphicsPixmapItem):
    def __init__(self, layer_id, path=None):
        super().__init__()
        self.layer_id = layer_id
        
        # [BARU] Default Time Properties
        self.start_time = 0.0
        self.duration = 5.0 # Default durasi
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable | 
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self._load_source(path)
        self.setZValue(0)

    def _load_source(self, path):
        if path and (path.endswith(".png") or path.endswith(".jpg")):
            self.setPixmap(QPixmap(path))
        else:
            pix = QPixmap(320, 180)
            pix.fill(QColor("#333333"))
            self.setPixmap(pix)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.setPen(QPen(QColor("#00aaff"), 3, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def update_properties(self, props: dict, z_index: int = 0):
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "rotation" in props: self.setRotation(props["rotation"])
        if "opacity" in props: self.setOpacity(props["opacity"])
        
        # [BARU] Update Data Waktu
        if "start_time" in props: self.start_time = float(props["start_time"])
        if "duration" in props: self.duration = float(props["duration"])
        
        self.setZValue(z_index)

    # [BARU] Logic Jantung Timeline: Show/Hide based on time
    def update_time(self, current_time):
        end_time = self.start_time + self.duration
        
        # Jika current_time ada di dalam range [start, end), TAMPILKAN.
        if self.start_time <= current_time < end_time:
            if not self.isVisible():
                self.setVisible(True)
        else:
            if self.isVisible():
                self.setVisible(False)