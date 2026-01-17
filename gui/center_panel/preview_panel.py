# gui/center_panel/preview_panel.py
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, 
    QComboBox, QCheckBox, QToolButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QBrush, QWheelEvent, QMouseEvent, QPen

# Import Canvas Items
from gui.center_panel.canvas_items.canvas_frame import CanvasFrameItem
from gui.center_panel.canvas_items.grid_item import GridItem

# Pastikan import class yang benar
try:
    from canvas.video_item import VideoLayerItem
except ImportError:
    # Fallback jika nama class di file anda masih VideoItem
    from canvas.video_item import VideoItem as VideoLayerItem

# =============================================================================
# CUSTOM VIEW: ZOOM & PAN LOGIC
# =============================================================================
class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        
        # 1. HILANGKAN SCROLLBARS (Tampilan Bersih)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Optimization Rendering
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Zoom mengikuti posisi mouse
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        
        # Background Abu Gelap
        self.setBackgroundBrush(QBrush(QColor("#151515")))
        
        # Pan State
        self._is_panning = False
        self._pan_start = QPointF()

    # 🔥 FIX UTAMA: MATIKAN AUTO-SCROLL SAAT GESER ITEM 🔥
    # Fungsi ini biasanya dipanggil otomatis saat item di-drag ke pinggir.
    # Kita kosongkan (pass) agar canvas DIAM DI TEMPAT.
    def ensureVisible(self, *args, **kwargs):
        pass

    # 2. SCROLL MOUSE = ZOOM
    def wheelEvent(self, event: QWheelEvent):
        # Zoom In/Out Logic
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)

    # 3. MANUAL PANNING (Klik Tengah / Alt+Klik)
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and event.modifiers() == Qt.AltModifier):
            self._is_panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            
            # Geser scrollbar secara manual
            hs = self.horizontalScrollBar()
            vs = self.verticalScrollBar()
            hs.setValue(hs.value() - delta.x())
            vs.setValue(vs.value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

# =============================================================================
# MAIN PREVIEW PANEL
# =============================================================================
class PreviewPanel(QWidget):
    sig_property_changed = Signal(str, dict) 
    sig_layer_selected = Signal(str)

    # Definisi Rasio Canvas
    CANVAS_PRESETS = {
        "9:16 (Tiktok/Reels)": (1080, 1920), # Default
        "16:9 (YouTube)": (1920, 1080),
        "1:1 (Instagram)": (1080, 1080),
        "4:5 (Portrait)": (1080, 1350),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)

        # Setup Scene
        self.scene = QGraphicsScene()
        
        # Gunakan Custom View yang sudah dimodifikasi
        self.view = ZoomableGraphicsView(self.scene)
        self.layout.addWidget(self.view)
        
        # Setup Default Canvas (1080x1920)
        self.canvas_frame = CanvasFrameItem(1080, 1920)
        self.scene.addItem(self.canvas_frame)

        self.grid = GridItem(1080, 1920)
        self.canvas_frame.set_grid(self.grid)
        
        self.video_service = None
        self.items_map = {} 

        self._init_toolbar()
        
        # Event Listener untuk seleksi item
        self.scene.selectionChanged.connect(self._on_internal_selection)

        # Auto Center saat aplikasi baru buka
        QTimer.singleShot(100, self._fit_view)

    def _init_toolbar(self):
        bar = QFrame()
        bar.setStyleSheet("background: #252526; border-top: 1px solid #3e4451;")
        bar.setFixedHeight(40)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 10, 0)
        
        # Ratio Selector
        self.combo_ratio = QComboBox()
        self.combo_ratio.addItems(self.CANVAS_PRESETS.keys())
        self.combo_ratio.setCurrentIndex(0) # Default 9:16
        self.combo_ratio.currentTextChanged.connect(self._on_ratio_changed)
        self.combo_ratio.setFixedWidth(150)
        layout.addWidget(self.combo_ratio)

        # Grid Toggle
        chk_grid = QCheckBox("Grid")
        chk_grid.setStyleSheet("color: #ccc;")
        chk_grid.toggled.connect(lambda v: setattr(self.grid, 'visible', v) or self.grid.update())
        layout.addWidget(chk_grid)

        layout.addStretch()
        
        # Fit Center Button
        btn_fit = QToolButton(text="🔍 Fit Center")
        btn_fit.setStyleSheet("color: white; border: 1px solid #555; padding: 3px;")
        btn_fit.clicked.connect(self._fit_view)
        layout.addWidget(btn_fit)
        
        self.layout.addWidget(bar)

    def _on_ratio_changed(self, ratio_text):
        w, h = self.CANVAS_PRESETS.get(ratio_text, (1080, 1920))
        self.canvas_frame.update_size(w, h)
        self._fit_view()

    def _fit_view(self):
        """Reset zoom dan posisikan canvas di tengah"""
        self.view.resetTransform()
        rect = self.canvas_frame.sceneBoundingRect()
        # Beri margin 10% agar tidak mepet
        margin = max(rect.width(), rect.height()) * 0.1
        view_rect = rect.adjusted(-margin, -margin, margin, margin)
        self.view.fitInView(view_rect, Qt.KeepAspectRatio)

    # --- CONTROLLER INTERFACE ---

    def set_video_service(self, service):
        self.video_service = service

    def on_time_changed(self, t):
        if not self.video_service: return
        for _, item in self.items_map.items():
            if item.isVisible() and isinstance(item, VideoLayerItem):
                start = getattr(item, 'start_time', 0.0)
                item.sync_frame(t - start, self.video_service)

    def sync_layer_visibility(self, active_ids):
        for lid, item in self.items_map.items():
            item.setVisible(lid in active_ids)

    def on_layer_created(self, layer_data):
        if layer_data.id in self.items_map: return

        # Buat Item
        item = VideoLayerItem(layer_data.id, layer_data.path)
        item.setParentItem(self.canvas_frame) # Attach ke frame
        
        props = layer_data.properties
        item.start_time = float(props.get("start_time", 0.0))
        item.update_transform(props)
        item.setZValue(layer_data.z_index)

        # Connect Sinyal Geser
        item.sig_transform_changed.connect(self.sig_property_changed)
        self.items_map[layer_data.id] = item

    def on_layer_removed(self, lid):
        if lid in self.items_map:
            item = self.items_map[lid]
            item.sig_transform_changed.disconnect() 
            self.scene.removeItem(item)
            del self.items_map[lid]

    def on_property_changed(self, layer_id, props):
        if layer_id in self.items_map:
            item = self.items_map[layer_id]
            item.blockSignals(True)
            item.update_transform(props)
            item.blockSignals(False)
            if "start_time" in props:
                item.start_time = float(props["start_time"])

    def on_selection_changed(self, layer_data):
        self.scene.blockSignals(True)
        self.scene.clearSelection()
        if layer_data and hasattr(layer_data, 'id'):
            lid = layer_data.id
            if lid in self.items_map:
                self.items_map[lid].setSelected(True)
        self.scene.blockSignals(False)
    
    def _on_internal_selection(self):
        items = self.scene.selectedItems()
        if items:
            item = items[0]
            if hasattr(item, 'layer_id'):
                self.sig_layer_selected.emit(item.layer_id)
        else:
            self.sig_layer_selected.emit(None)