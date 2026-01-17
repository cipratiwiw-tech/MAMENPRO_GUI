from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtGui import QPixmap, QColor, QPen
from PySide6.QtCore import Qt

# Import Service yang baru kita buat
from engine.video_service import VideoService

class VideoItem(QGraphicsPixmapItem):
    def __init__(self, layer_id, path=None):
        super().__init__()
        self.layer_id = layer_id
        self.path = path
        
        # [KEMBALI] Kita butuh ini HANYA untuk hitungan matematika (Offset)
        # Bukan untuk menentukan kapan show/hide.
        self.start_offset = 0.0 
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable | 
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self._load_dummy_content()
        
    def _load_dummy_content(self):
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
        
        # 2. Update Offset Waktu
        if "start_time" in props: 
            self.start_offset = float(props["start_time"])
        
        # 3. Z-Index
        if z_index is not None:
            self.setZValue(z_index)

    def sync_frame(self, global_time: float):
        """
        Jantung Render Item.
        Minta gambar ke VideoService sesuai waktu saat ini.
        """
        # Hitung waktu relatif (Local Time)
        # Contoh: Global 5.0s, Layer mulai di 2.0s -> Video frame ke 3.0s
        local_time = global_time - self.start_offset
        
        # Jangan minta frame minus (sebelum video mulai)
        if local_time < 0: local_time = 0
        
        # Panggil Pelayan (VideoService)
        # Ini akan mengembalikan QPixmap asli dari video!
        pix = VideoService.get_frame(self.path, local_time)
        
        self.setPixmap(pix)