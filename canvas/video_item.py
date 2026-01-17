from PySide6.QtCore import QObject, Signal, Qt, QPointF
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QStyle
from PySide6.QtGui import QPixmap, QColor, QPen

# Import Gizmo
try:
    from gui.center_panel.canvas_items.transform_gizmo import TransformGizmo
except ImportError:
    TransformGizmo = None


class VideoLayerItem(QObject, QGraphicsPixmapItem):
    sig_transform_changed = Signal(str, dict)

    def __init__(self, layer_id, path, parent=None):
        QObject.__init__(self)
        QGraphicsPixmapItem.__init__(self, parent)

        # --- ID ---
        self.layer_id = layer_id
        self.file_path = path
        self.start_time = 0.0

        # --- GIZMO ---
        self.gizmo = None

        # --- COLOR CONFIG (🔥 JANGAN DIHAPUS)
        self.color_config = {
            "color": {
                "brightness": 0,
                "contrast": 0,
                "saturation": 0,
                "hue": 0,
                "temperature": 0,
            },
            "effect": {
                "blur": 0,
                "vignette": 0,
            }
        }

        # --- GRAPHICS CONFIG ---
        self.setZValue(0)
        self.setTransformationMode(Qt.SmoothTransformation)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )

        self._set_placeholder()

    # ======================================================
    # 🔑 TRANSFORM ORIGIN
    # ======================================================

    def _update_origin(self):
        br = self.boundingRect()
        if not br.isNull():
            self.setTransformOriginPoint(br.center())
            if self.gizmo and hasattr(self.gizmo, "refresh"):
                self.gizmo.refresh()

    def _set_placeholder(self):
        pix = QPixmap(320, 180)
        pix.fill(QColor("#333333"))
        self.setPixmap(pix)
        self._update_origin()

    # ======================================================
    # 🎯 ITEM CHANGE (SNAP + GIZMO)
    # ======================================================

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            selected = bool(value)

            if selected:
                self._update_origin()
                if not self.gizmo and TransformGizmo:
                    self.gizmo = TransformGizmo(self)
            else:
                if self.gizmo:
                    self.scene().removeItem(self.gizmo)
                    self.gizmo = None

        return super().itemChange(change, value)

    # ======================================================
    # 🎨 SYNC FRAME (🔥 COLOR HIDUP DI SINI)
    # ======================================================

    def sync_frame(self, relative_time: float, video_service):
        if not video_service:
            return

        qimg = video_service.get_frame(
            self.layer_id,
            relative_time,
            self.color_config   # 🔥 INI KUNCI COLOR GRADING
        )

        if qimg and not qimg.isNull():
            self.setPixmap(QPixmap.fromImage(qimg))
            self._update_origin()

    # ======================================================
    # 🔧 UPDATE DARI CONTROLLER (TRANSFORM + COLOR)
    # ======================================================

    def update_transform(self, props: dict):
        # --- TRANSFORM ---
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "rotation" in props: self.setRotation(props["rotation"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "start_time" in props: self.start_time = float(props["start_time"])

        # --- COLOR ---
        c = self.color_config["color"]
        e = self.color_config["effect"]

        for k in c:
            if k in props:
                c[k] = props[k]

        for k in e:
            if k in props:
                e[k] = props[k]

        self._update_origin()

    # ======================================================
    # 📡 NOTIFY (DIPANGGIL GIZMO)
    # ======================================================

    def notify_transform_change(self):
        self.sig_transform_changed.emit(self.layer_id, {
            "x": self.pos().x(),
            "y": self.pos().y(),
            "rotation": self.rotation(),
            "scale": int(self.scale() * 100)
        })

    # ======================================================
    # 🎨 PAINT (BORDER SAAT SELECT)
    # ======================================================

    def paint(self, painter, option, widget=None):
        if option.state & QStyle.State_HasFocus:
            option.state &= ~QStyle.State_HasFocus

        QGraphicsPixmapItem.paint(self, painter, option, widget)

        if self.isSelected():
            painter.setPen(QPen(QColor("#00a8ff"), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())
