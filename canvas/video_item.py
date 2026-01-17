from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtGui import QPixmap, QColor, QPen
from PySide6.QtCore import Qt

class VideoItem(QGraphicsPixmapItem):
    def __init__(self, layer_id, path=None):
        super().__init__()
        self.layer_id = layer_id
        self.path = path
        
        # ❌ HAPUS: self.start_time & self.duration
        # VideoItem tidak perlu tahu kapan dia mulai di timeline global.
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable | 
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self._load_dummy_content()
        
    def _load_dummy_content(self):
        # Placeholder Hitam (sebelum engine video decoding aktif)
        pix = QPixmap(320, 180)
        pix.fill(QColor("#333333"))
        self.setPixmap(pix)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.setPen(QPen(QColor("#00aaff"), 3, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def update_properties(self, props: dict, z_index: int = None):
        # 1. Transform
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "rotation" in props: self.setRotation(props["rotation"])
        if "opacity" in props: self.setOpacity(props["opacity"])
        
        # ❌ HAPUS: if "start_time" ...
        # ❌ HAPUS: if "duration" ...
        
        # 2. Z-Index
        if z_index is not None:
            self.setZValue(z_index)

    def sync_frame(self, t: float):
        """
        Terima waktu 't' apa adanya.
        Nanti logic: local_time = t - layer_start_time
        akan dilakukan di luar atau di sini via parameter tambahan, 
        tapi JANGAN simpan state waktu di self.
        """
        # (TODO FUTURE) Request frame ke VideoEngine
        # frame = VideoDecoder.get_frame(self.path, t)
        # self.setPixmap(frame)
        pass