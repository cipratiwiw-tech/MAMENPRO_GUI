from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtGui import QPixmap, QColor, QPen
from PySide6.QtCore import Qt, QObject, Signal

# Inherit QObject agar bisa pakai Signal
class VideoLayerItem(QObject, QGraphicsPixmapItem):
    # Signal: layer_id (str), properties (dict)
    sig_transform_changed = Signal(str, dict)

    def __init__(self, layer_id, path, parent=None):
        QObject.__init__(self)
        QGraphicsPixmapItem.__init__(self, parent)
        
        self.layer_id = layer_id
        self.file_path = path
        self.start_time = 0.0
        
        self.setZValue(0) 

        # --- INTERAKSI ---
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        self.setTransformOriginPoint(self.boundingRect().center())
        self._set_placeholder()

    def _set_placeholder(self):
        pix = QPixmap(320, 180)
        pix.fill(QColor("#333333"))
        self.setPixmap(pix)
        self._update_origin()

    def _update_origin(self):
        rect = self.boundingRect()
        self.setTransformOriginPoint(rect.center())

    def sync_frame(self, t, video_service):
        if not video_service: return
        qimg = video_service.get_frame_image(self.file_path, t)
        if qimg and not qimg.isNull():
            self.setPixmap(QPixmap.fromImage(qimg))
            self._update_origin()

    def update_transform(self, props: dict):
        # Update posisi tanpa memicu signal balik
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "rotation" in props: self.setRotation(props["rotation"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "opacity" in props: self.setOpacity(props["opacity"])

    # ✅ [PERBAIKAN 2] Pastikan mengirim DICT saat lepas mouse
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        
        # Bungkus data dalam dictionary
        final_props = {
            "x": self.pos().x(),
            "y": self.pos().y(),
            "rotation": self.rotation(),
            "scale": int(self.scale() * 100)
        }
        
        # Kirim sinyal (str, dict)
        self.sig_transform_changed.emit(self.layer_id, final_props)

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.setPen(QPen(QColor("#00AEEF"), 3, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())