# canvas/video_item.py
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtGui import QPixmap, QColor, QPen

# Import Gizmo Baru
try:
    from gui.center_panel.canvas_items.transform_gizmo import TransformGizmo
except ImportError:
    # Fallback agar tidak crash jika file gizmo belum ada/salah nama
    TransformGizmo = None
    print("⚠️ TransformGizmo not found/imported")

class VideoLayerItem(QObject, QGraphicsPixmapItem): 
    sig_transform_changed = Signal(str, dict)

    def __init__(self, layer_id, path, parent=None):
        QObject.__init__(self)
        QGraphicsPixmapItem.__init__(self, parent)
        
        # 🔥 FIX: DEFINISIKAN GIZMO DI AWAL SEBELUM METHOD LAIN DIPANGGIL 🔥
        self.gizmo = None
        
        self.setTransformationMode(Qt.SmoothTransformation)
        
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
        
        # Sekarang aman dipanggil karena self.gizmo sudah ada (None)
        self._set_placeholder()

    def _set_placeholder(self):
        pix = QPixmap(320, 180)
        pix.fill(QColor("#333333"))
        self.setPixmap(pix)
        self._update_origin()

    def _update_origin(self):
        rect = self.boundingRect()
        self.setTransformOriginPoint(rect.center())
        # Update layout gizmo jika ukuran gambar berubah
        if self.gizmo:
            self.gizmo._update_layout()

    def sync_frame(self, t, video_service):
        if not video_service: return
        qimg = video_service.get_frame_image(self.file_path, t)
        if qimg and not qimg.isNull():
            self.setPixmap(QPixmap.fromImage(qimg))
            self._update_origin()

    def update_transform(self, props: dict):
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "rotation" in props: self.setRotation(props["rotation"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "opacity" in props: self.setOpacity(props["opacity"])

    # --- ITEM CHANGE EVENT (AUTO SHOW/HIDE GIZMO) ---
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            is_selected = bool(value)
            if is_selected:
                # Jika terpilih, buat Gizmo
                if not self.gizmo and TransformGizmo:
                    self.gizmo = TransformGizmo(self)
            else:
                # Jika tidak terpilih, hapus Gizmo
                if self.gizmo:
                    if self.scene():
                        self.scene().removeItem(self.gizmo)
                    self.gizmo = None
                    
        return super().itemChange(change, value)

    # --- SAVE LOGIC ---

    def notify_transform_change(self):
        """Dipanggil oleh Gizmo saat selesai drag"""
        self._emit_changes()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._emit_changes()

    def _emit_changes(self):
        final_props = {
            "x": self.pos().x(),
            "y": self.pos().y(),
            "rotation": self.rotation(),
            "scale": int(self.scale() * 100)
        }
        self.sig_transform_changed.emit(self.layer_id, final_props)

    def paint(self, painter, option, widget):
        # Render gambar seperti biasa
        super().paint(painter, option, widget)