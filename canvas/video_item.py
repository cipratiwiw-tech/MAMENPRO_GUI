# canvas/video_item.py
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QStyle
from PySide6.QtGui import QPixmap, QColor, QPen
from PySide6.QtCore import Qt, Signal, QObject

# [FIX] Tambahkan QObject agar bisa pakai Signal
class VideoLayerItem(QObject, QGraphicsPixmapItem):
    sig_transform_changed = Signal(str, dict)

    def __init__(self, layer_id, path):
        # [FIX] Init kedua parent class
        QObject.__init__(self)
        QGraphicsPixmapItem.__init__(self)
        
        self.layer_id = layer_id
        self.file_path = path
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        self.start_time = 0.0
        
        # Init Config Default
        self.color_config = {
            "color": {"brightness": 0, "contrast": 0, "saturation": 0, "hue": 0, "temperature": 0},
            "effect": {"blur": 0, "vignette": 0}
        }

    def paint(self, painter, option, widget=None):
        if option.state & QStyle.State_HasFocus:
            option.state &= ~QStyle.State_HasFocus
            
        # Panggil paint dari QGraphicsPixmapItem explicit
        QGraphicsPixmapItem.paint(self, painter, option, widget)
        
        if self.isSelected():
            painter.setPen(QPen(QColor("#00a8ff"), 3, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def update_transform(self, props: dict):
        # 1. Transform Visual
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "rotation" in props: self.setRotation(props["rotation"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "start_time" in props: self.start_time = float(props["start_time"])
        
        # 2. Update Color Config
        c = self.color_config["color"]
        e = self.color_config["effect"]
        
        if "brightness" in props: c["brightness"] = props["brightness"]
        if "contrast" in props: c["contrast"] = props["contrast"]
        if "saturation" in props: c["saturation"] = props["saturation"]
        if "hue" in props: c["hue"] = props["hue"]
        if "temperature" in props: c["temperature"] = props["temperature"]
        if "blur" in props: e["blur"] = props["blur"]
        if "vignette" in props: e["vignette"] = props["vignette"]

    def sync_frame(self, relative_time: float, video_service):
        if not video_service: return
        
        # Request frame dengan config
        qimg = video_service.get_frame(self.layer_id, relative_time, self.color_config)
        
        if not qimg.isNull():
            self.setPixmap(QPixmap.fromImage(qimg))
            
    def itemChange(self, change, value):
        return QGraphicsPixmapItem.itemChange(self, change, value)
    
    def mouseReleaseEvent(self, event):
        QGraphicsPixmapItem.mouseReleaseEvent(self, event)
        self.sig_transform_changed.emit(self.layer_id, {
            "x": self.x(),
            "y": self.y(),
            "rotation": self.rotation(),
            "scale": int(self.scale() * 100)
        })