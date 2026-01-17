# gui/center_panel/preview_panel.py
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, 
    QComboBox, QCheckBox, QToolButton, QFrame, QSizePolicy, QLabel, QMenu
)
from PySide6.QtCore import Qt, Signal, QTimer, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QWheelEvent, QMouseEvent, QPen, QAction, QKeySequence
)

# Import Canvas Items
from gui.center_panel.canvas_items.canvas_frame import CanvasFrameItem
from gui.center_panel.canvas_items.grid_item import GridItem

try:
    from canvas.video_item import VideoLayerItem
except ImportError:
    from canvas.video_item import VideoItem as VideoLayerItem

# =============================================================================
# VIEW: LOCKED CENTER
# =============================================================================
class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        self.setAlignment(Qt.AlignCenter)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        
        self.setBackgroundBrush(QBrush(QColor("#151515")))

    def ensureVisible(self, *args, **kwargs):
        pass

    def wheelEvent(self, event: QWheelEvent):
        zoom_in = 1.15
        zoom_out = 1 / zoom_in
        if event.angleDelta().y() > 0:
            self.scale(zoom_in, zoom_in)
        else:
            self.scale(zoom_out, zoom_out)

# =============================================================================
# MAIN PREVIEW PANEL
# =============================================================================
class PreviewPanel(QWidget):
    sig_property_changed = Signal(str, dict) 
    sig_layer_selected = Signal(str)
    sig_request_delete = Signal(str) 

    CANVAS_PRESETS = {
        "9:16 (Tiktok/Reels)": (1080, 1920),
        "16:9 (YouTube)": (1920, 1080),
        "1:1 (Instagram)": (1080, 1080),
        "4:5 (Portrait)": (1080, 1350),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)

        # 1. Setup Scene
        self.scene = QGraphicsScene()
        huge_size = 50000 
        self.scene.setSceneRect(-huge_size, -huge_size, huge_size * 2, huge_size * 2)
        
        # 2. Setup View
        self.view = ZoomableGraphicsView(self.scene)
        self.layout.addWidget(self.view)
        
        # 3. Setup Canvas Frame
        self.canvas_width = 1080
        self.canvas_height = 1920
        self.canvas_frame = CanvasFrameItem(self.canvas_width, self.canvas_height)
        self.scene.addItem(self.canvas_frame)

        self.grid = GridItem(self.canvas_width, self.canvas_height)
        self.canvas_frame.set_grid(self.grid)
        
        self._center_canvas_item()

        self.video_service = None
        self.items_map = {} 

        # 4. Init Toolbar
        self._init_toolbar()
        
        self.scene.selectionChanged.connect(self._on_internal_selection)
        QTimer.singleShot(100, self._fit_view)

    def _init_toolbar(self):
        bar = QFrame()
        bar.setStyleSheet("background: #252526; border-top: 1px solid #3e4451;")
        bar.setFixedHeight(45)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 10, 0)
        
        self.combo_ratio = QComboBox()
        self.combo_ratio.addItems(self.CANVAS_PRESETS.keys())
        self.combo_ratio.setCurrentIndex(0)
        self.combo_ratio.currentTextChanged.connect(self._on_ratio_changed)
        self.combo_ratio.setFixedWidth(140)
        layout.addWidget(self.combo_ratio)

        chk_grid = QCheckBox("Grid")
        chk_grid.setStyleSheet("color: #ccc; margin-left: 5px;")
        chk_grid.toggled.connect(lambda v: setattr(self.grid, 'visible', v) or self.grid.update())
        layout.addWidget(chk_grid)

        layout.addStretch()
        
        self.lbl_time = QLabel("00:00:00")
        self.lbl_time.setAlignment(Qt.AlignCenter)
        self.lbl_time.setFixedWidth(100) 
        self.lbl_time.setStyleSheet("""
            QLabel {
                color: #00AEEF; 
                font-weight: bold; 
                font-family: Consolas, Monospace; 
                font-size: 16px;
                background: #151515;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 2px 0px;
            }
        """)
        layout.addWidget(self.lbl_time)
        
        layout.addStretch()
        
        btn_fit = QToolButton(text="🔍 Fit View")
        btn_fit.setStyleSheet("""
            QToolButton { color: white; border: 1px solid #555; border-radius: 3px; padding: 4px 8px; }
            QToolButton:hover { background: #3e4451; }
        """)
        btn_fit.clicked.connect(self._fit_view)
        layout.addWidget(btn_fit)
        
        self.layout.addWidget(bar)

    def contextMenuEvent(self, event):
        scene_pos = self.view.mapToScene(event.pos())
        items = self.scene.items(scene_pos)
        
        target_item = None
        for i in items:
            if isinstance(i, VideoLayerItem):
                target_item = i
                break
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2D2D30; color: #EEE; border: 1px solid #454545; }
            QMenu::item { padding: 6px 24px; }
            QMenu::item:selected { background-color: #007ACC; }
        """)

        if target_item:
            act_reset = QAction("↺ Reset Transform", self)
            act_reset.triggered.connect(lambda: self._action_reset(target_item))
            menu.addAction(act_reset)
            
            act_center = QAction("🎯 Center to Canvas", self)
            act_center.triggered.connect(lambda: self._action_center(target_item))
            menu.addAction(act_center)
            
            act_fit = QAction("↔ Fit to Canvas", self)
            act_fit.triggered.connect(lambda: self._action_fit(target_item))
            menu.addAction(act_fit)
            
            menu.addSeparator()
            
            act_del = QAction("🗑️ Delete", self)
            act_del.setShortcut(QKeySequence.Delete)
            act_del.triggered.connect(lambda: self.sig_request_delete.emit(target_item.layer_id))
            menu.addAction(act_del)
            
        else:
            act_fit_view = QAction("🔍 Fit View", self)
            act_fit_view.triggered.connect(self._fit_view)
            menu.addAction(act_fit_view)
        
        menu.exec(event.globalPos())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            selected_items = self.scene.selectedItems()
            if selected_items:
                for item in selected_items:
                    if hasattr(item, 'layer_id'):
                        self.sig_request_delete.emit(item.layer_id)
                        self.on_layer_removed(item.layer_id)
        else:
            super().keyPressEvent(event)

    def _action_reset(self, item):
        props = {"scale": 100, "rotation": 0}
        self.sig_property_changed.emit(item.layer_id, props)

    def _action_center(self, item):
        frame_rect = self.canvas_frame.rect()
        canvas_cx = frame_rect.width() / 2
        canvas_cy = frame_rect.height() / 2
        item_rect = item.boundingRect()
        final_x = canvas_cx - (item_rect.width() / 2)
        final_y = canvas_cy - (item_rect.height() / 2)
        props = {"x": final_x, "y": final_y}
        self.sig_property_changed.emit(item.layer_id, props)

    def _action_fit(self, item):
        frame_rect = self.canvas_frame.rect()
        item_rect = item.boundingRect()
        if item_rect.width() > 0 and item_rect.height() > 0:
            ratio_w = frame_rect.width() / item_rect.width()
            ratio_h = frame_rect.height() / item_rect.height()
            final_ratio = min(ratio_w, ratio_h)
            
            canvas_cx = frame_rect.width() / 2
            canvas_cy = frame_rect.height() / 2
            final_x = canvas_cx - (item_rect.width() / 2)
            final_y = canvas_cy - (item_rect.height() / 2)
            
            props = {
                "scale": int(final_ratio * 100),
                "rotation": 0,
                "x": final_x,
                "y": final_y
            }
            self.sig_property_changed.emit(item.layer_id, props)

    def _center_canvas_item(self):
        cx = -self.canvas_width / 2
        cy = -self.canvas_height / 2
        self.canvas_frame.setPos(cx, cy)

    def _on_ratio_changed(self, ratio_text):
        w, h = self.CANVAS_PRESETS.get(ratio_text, (1080, 1920))
        self.canvas_width = w
        self.canvas_height = h
        self.canvas_frame.update_size(w, h)
        self._center_canvas_item()
        self._fit_view()

    def _fit_view(self):
        self.view.resetTransform()
        rect = self.canvas_frame.sceneBoundingRect()
        margin = max(rect.width(), rect.height()) * 0.1
        view_rect = rect.adjusted(-margin, -margin, margin, margin)
        self.view.fitInView(view_rect, Qt.KeepAspectRatio)

    def set_video_service(self, service):
        self.video_service = service

    def on_time_changed(self, t):
        if self.video_service:
            for _, item in self.items_map.items():
                if item.isVisible() and isinstance(item, VideoLayerItem):
                    start = getattr(item, 'start_time', 0.0)
                    item.sync_frame(t - start, self.video_service)
        
        total_seconds = int(t)
        rem_ms = int((t - total_seconds) * 100)
        mins = total_seconds // 60
        secs = total_seconds % 60
        self.lbl_time.setText(f"{mins:02d}:{secs:02d}:{rem_ms:02d}")

    def sync_layer_visibility(self, active_ids):
        for lid, item in self.items_map.items():
            item.setVisible(lid in active_ids)

    def on_layer_created(self, layer_data):
        if layer_data.id in self.items_map: return
        item = VideoLayerItem(layer_data.id, layer_data.path)
        item.setParentItem(self.canvas_frame) 
        props = layer_data.properties
        item.start_time = float(props.get("start_time", 0.0))
        item.update_transform(props)
        item.setZValue(layer_data.z_index)
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
            
            # [BARU] Update Z-Index jika ada (untuk sinkronisasi Z-Order)
            if "z_index" in props:
                item.setZValue(props["z_index"])
                
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