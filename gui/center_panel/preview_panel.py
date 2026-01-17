# gui/center_panel/preview_panel.py
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, 
    QGraphicsItem, QGraphicsRectItem, QToolButton, QGraphicsSimpleTextItem
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QBrush, QPen, QColor, QPainter, QPixmap, QImage, QFont
)

# ==========================================
# CONSTANTS & CONFIG
# ==========================================
COLOR_ACCENT = QColor("#56b6c2")
COLOR_BG = QColor("#1e1e1e")
COLOR_SAFE = QColor(0, 255, 0, 60)
COLOR_GUIDE = QColor(255, 255, 255, 50)
HANDLE_SIZE = 12

class HandleType:
    TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT, ROTATE = range(1, 6)

# ==========================================
# 1. PASSIVE VIDEO ITEM
# ==========================================
class VideoItem(QGraphicsRectItem):
    """
    Hanya container visual. 
    Tidak punya akses ke Service/Engine.
    Menerima QPixmap matang untuk ditampilkan.
    """
    def __init__(self, layer_id, layer_type, width=1280, height=720):
        super().__init__(0, 0, width, height)
        self.layer_id = layer_id
        self.layer_type = layer_type
        self.current_pixmap = None
        
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.setBrush(QColor(30, 30, 30)) # Placeholder
        self.setPen(Qt.NoPen)

    def set_frame(self, frame):
        """Menerima data visual mentah (QPixmap/QImage)"""
        if isinstance(frame, QImage):
            self.current_pixmap = QPixmap.fromImage(frame)
        elif isinstance(frame, QPixmap):
            self.current_pixmap = frame
        else:
            self.current_pixmap = None # Clear/Black
        self.update() # Trigger repaint

    def paint(self, painter, option, widget):
        if self.current_pixmap and not self.current_pixmap.isNull():
            painter.drawPixmap(self.rect().toRect(), self.current_pixmap)
        else:
            super().paint(painter, option, widget)
            painter.setPen(Qt.white)
            painter.drawText(self.boundingRect(), Qt.AlignCenter, f"{self.layer_type}\n{self.layer_id}")

        # Hint border
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.rect())


# ==========================================
# 2. GIZMOS (UI HELPER)
# ==========================================
class TransformHandle(QGraphicsRectItem):
    def __init__(self, h_type, parent=None):
        super().__init__(-HANDLE_SIZE/2, -HANDLE_SIZE/2, HANDLE_SIZE, HANDLE_SIZE, parent)
        self.setBrush(QBrush(COLOR_ACCENT))
        self.setPen(QPen(Qt.black, 1))
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)

class SelectionGizmo(QGraphicsRectItem):
    def __init__(self, target=None):
        super().__init__()
        self.target = target
        self.setPen(QPen(COLOR_ACCENT, 2, Qt.DashLine))
        self.setBrush(Qt.NoBrush)
        self.handles = [TransformHandle(i, self) for i in range(1, 6)]
        if target: self.sync()

    def sync(self):
        if not self.target: return
        self.setRect(self.target.boundingRect())
        self.setPos(self.target.pos())
        self.setRotation(self.target.rotation())
        self.setScale(self.target.scale())
        self.setTransformOriginPoint(self.target.transformOriginPoint())
        
        r = self.rect()
        positions = {
            1: r.topLeft(), 2: r.topRight(), 3: r.bottomLeft(), 4: r.bottomRight(),
            5: QPointF(r.center().x(), r.top() - 25)
        }
        for i, h in enumerate(self.handles): h.setPos(positions[i+1])

class GuideOverlay(QGraphicsItem):
    def __init__(self, w=1920, h=1080):
        super().__init__()
        self.w, self.h = w, h
        self.visible = False
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setZValue(9999)

    def boundingRect(self): return QRectF(0, 0, self.w, self.h)
    
    def paint(self, painter, option, widget):
        if not self.visible: return
        painter.setPen(QPen(COLOR_GUIDE, 1, Qt.DashLine))
        painter.drawLine(self.w/2, 0, self.w/2, self.h)
        painter.drawLine(0, self.h/2, self.w, self.h/2)
        
        painter.setPen(QPen(COLOR_SAFE, 1))
        m_w, m_h = self.w*0.05, self.h*0.05
        painter.drawRect(QRectF(m_w, m_h, self.w-2*m_w, self.h-2*m_h))

# ==========================================
# 3. PREVIEW PANEL (MAIN CLASS)
# ==========================================
class PreviewPanel(QWidget):
    sig_layer_selected = Signal(str)
    sig_preview_command = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        # Init View
        self.scene = QGraphicsScene(0, 0, 1920, 1080)
        self.scene.setBackgroundBrush(QBrush(COLOR_BG))
        self.view = QGraphicsView(self.scene)
        self.view.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.view)
        
        # Overlays
        self.guide = GuideOverlay()
        self.scene.addItem(self.guide)
        self.warning = QGraphicsSimpleTextItem("SERVICE DISCONNECTED")
        self.warning.setBrush(QBrush(Qt.red))
        self.warning.setFont(QFont("Arial", 20, QFont.Bold))
        self.scene.addItem(self.warning)
        
        # State
        self.items_map = {}
        self.active_gizmo = None
        self.video_service = None # Injected later
        
        # Internal Events
        self.scene.selectionChanged.connect(self._on_internal_select)
        self._init_toolbar()

    def _init_toolbar(self):
        bar = QWidget()
        bar.setStyleSheet("background:#252526;")
        layout = QHBoxLayout(bar)
        
        btn_play = QToolButton(text="▶ Play")
        btn_play.clicked.connect(lambda: self.sig_preview_command.emit("play"))
        
        btn_guide = QToolButton(text="# Guide")
        btn_guide.setCheckable(True)
        btn_guide.toggled.connect(lambda c: setattr(self.guide, 'visible', c) or self.guide.update())
        
        btn_fit = QToolButton(text="🔍 Fit")
        btn_fit.clicked.connect(lambda: self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio))
        
        layout.addWidget(btn_play)
        layout.addStretch()
        layout.addWidget(btn_guide)
        layout.addWidget(btn_fit)
        self.layout.addWidget(bar)

    # --- PUBLIC API (Dipanggil Binder) ---
    
    def set_video_service(self, service):
        """Dependency Injection point"""
        self.video_service = service
        self.warning.setVisible(not service)

    def on_time_changed(self, t):
        """Menerima waktu -> Minta Frame -> Update Item"""
        if not self.video_service: return

        # Loop hanya item yang sedang visible (sudah disaring via sync_layer_visibility)
        for lid, item in self.items_map.items():
            if item.isVisible():
                try:
                    # FETCH FRAME DARI SERVICE
                    frame = self.video_service.get_preview_frame(lid, t)
                    item.set_frame(frame)
                except Exception:
                    item.set_frame(None)

    def sync_layer_visibility(self, active_ids):
        """Menerima daftar ID aktif dari TimelineEngine (via Controller)"""
        for lid, item in self.items_map.items():
            item.setVisible(lid in active_ids)

    def on_layer_created(self, data):
        if data.id in self.items_map: return
        item = VideoItem(data.id, getattr(data, 'type', 'media'))
        props = data.properties
        item.setPos(props.get('x',0), props.get('y',0))
        item.setZValue(data.z_index)
        self.scene.addItem(item)
        self.items_map[data.id] = item

    def on_layer_removed(self, lid):
        if lid in self.items_map:
            if self.active_gizmo and self.active_gizmo.target == self.items_map[lid]:
                self.scene.removeItem(self.active_gizmo)
                self.active_gizmo = None
            self.scene.removeItem(self.items_map[lid])
            del self.items_map[lid]

    def on_property_changed(self, lid, props):
        if lid in self.items_map:
            item = self.items_map[lid]
            if 'x' in props: item.setX(props['x'])
            if 'y' in props: item.setY(props['y'])
            if 'scale' in props: item.setScale(props['scale'])
            if 'rotation' in props: item.setRotation(props['rotation'])
            if self.active_gizmo and self.active_gizmo.target == item:
                self.active_gizmo.sync()

    def on_selection_changed(self, data):
        self.scene.blockSignals(True)
        self.scene.clearSelection()
        if data and data.id in self.items_map:
            item = self.items_map[data.id]
            item.setSelected(True)
            self._update_gizmo(item)
        else:
            self._update_gizmo(None)
        self.scene.blockSignals(False)

    # --- INTERNAL LOGIC ---
    def _on_internal_select(self):
        sel = self.scene.selectedItems()
        target = sel[0] if sel and isinstance(sel[0], VideoItem) else None
        self._update_gizmo(target)
        self.sig_layer_selected.emit(target.layer_id if target else None)

    def _update_gizmo(self, target):
        if self.active_gizmo: 
            self.scene.removeItem(self.active_gizmo)
            self.active_gizmo = None
        if target:
            self.active_gizmo = SelectionGizmo(target)
            self.scene.addItem(self.active_gizmo)

    def resizeEvent(self, e):
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        super().resizeEvent(e)