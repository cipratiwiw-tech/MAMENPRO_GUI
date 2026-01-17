# canvas/video_item.py
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtGui import QPixmap, QColor, QPen, QBrush
from PySide6.QtCore import Qt

class VideoItem(QGraphicsPixmapItem):
    """
    Representasi visual untuk Image atau Video (Frame statis) di Canvas.
    Inherit dari QGraphicsPixmapItem agar mudah menampilkan gambar.
    """
    def __init__(self, layer_id, path=None):
        super().__init__()
        self.layer_id = layer_id
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable | 
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        # Load visual
        self._load_source(path)
        
        # Style default
        self.setShapeMode(QGraphicsPixmapItem.BoundingRectShape)

    def _load_source(self, path):
        if path and (path.endswith(".png") or path.endswith(".jpg")):
            # Jika image, load langsung
            self.setPixmap(QPixmap(path))
        else:
            # Jika video atau path kosong, buat placeholder kotak abu-abu
            pix = QPixmap(200, 150)
            pix.fill(QColor("#333333"))
            self.setPixmap(pix)

    def paint(self, painter, option, widget=None):
        # Render gambar aslinya
        super().paint(painter, option, widget)

        # Render garis seleksi jika item ini dipilih
        if self.isSelected():
            painter.setPen(QPen(QColor("#00aaff"), 3, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def itemChange(self, change, value):
        # (Opsional) Jika visual digeser user, kita bisa emit sinyal via scene
        # Tapi untuk strict SRP, Canvas itu pasif. Biarkan Binder/Controller yang nanti ambil posisi saat save/render.
        # Atau gunakan sinyal 'geometryChanged' dari QGraphicsObject jika perlu real-time feedback ke panel setting.
        return super().itemChange(change, value)
    
    # --- API UNTUK PREVIEW PANEL ---
    def update_properties(self, props: dict):
        """Menerima update data dari Logic -> Visual"""
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "rotation" in props: self.setRotation(props["rotation"])
        if "opacity" in props: self.setOpacity(props["opacity"])