import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, 
    QComboBox, QCheckBox, QToolButton, QGraphicsItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QBrush

# Import komponen Canvas & Grid
from gui.center_panel.canvas_items.canvas_frame import CanvasFrameItem
from gui.center_panel.canvas_items.grid_item import GridItem
from canvas.video_item import VideoLayerItem 

class PreviewPanel(QWidget):
    # Signal ke Controller (WAJIB: str, dict)
    sig_property_changed = Signal(str, dict) 
    sig_layer_selected = Signal(str)

    CANVAS_PRESETS = {
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
        "1:1": (1080, 1080),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)

        # 1. Setup Scene
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.view.setAlignment(Qt.AlignCenter)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        
        # 2. Setup Canvas Frame
        self.canvas_frame = CanvasFrameItem(1920, 1080)
        self.scene.addItem(self.canvas_frame)

        # 3. Setup Grid
        self.grid = GridItem(1920, 1080)
        self.canvas_frame.set_grid(self.grid)
        
        # 4. State
        self.video_service = None
        self.items_map = {} 

        self._init_toolbar()
        self.layout.addWidget(self.view)
        
        # Connect Selection Scene -> UI
        self.scene.selectionChanged.connect(self._on_internal_selection)

    def _init_toolbar(self):
        bar = QWidget()
        bar.setStyleSheet("background: #252526; border-bottom: 1px solid #3e4451;")
        layout = QHBoxLayout(bar)
        
        self.combo_ratio = QComboBox()
        self.combo_ratio.addItems(self.CANVAS_PRESETS.keys())
        self.combo_ratio.currentTextChanged.connect(self._on_ratio_changed)
        layout.addWidget(self.combo_ratio)

        chk_grid = QCheckBox("Grid")
        chk_grid.toggled.connect(lambda v: setattr(self.grid, 'visible', v) or self.grid.update())
        layout.addWidget(chk_grid)

        layout.addStretch()
        
        btn_fit = QToolButton(text="Fit")
        btn_fit.clicked.connect(self._fit_view)
        layout.addWidget(btn_fit)
        
        self.layout.addWidget(bar)

    def _on_ratio_changed(self, ratio_text):
        w, h = self.CANVAS_PRESETS.get(ratio_text, (1920, 1080))
        self.canvas_frame.update_size(w, h)
        self._fit_view()

    def _fit_view(self):
        self.view.fitInView(self.canvas_frame, Qt.KeepAspectRatio)

    # --- CONTROLLER / BINDER API ---

    def set_video_service(self, service):
        self.video_service = service

    def on_time_changed(self, t):
        if not self.video_service: return
        for _, item in self.items_map.items():
            if item.isVisible() and isinstance(item, VideoLayerItem):
                # Hitung waktu relatif layer
                start = getattr(item, 'start_time', 0.0)
                item.sync_frame(t - start, self.video_service)

    def sync_layer_visibility(self, active_ids):
        for lid, item in self.items_map.items():
            item.setVisible(lid in active_ids)

    def on_layer_created(self, layer_data):
        if layer_data.id in self.items_map: return

        # Buat Item
        if layer_data.type == "video":
            item = VideoLayerItem(layer_data.id, layer_data.path)
        else:
            item = VideoLayerItem(layer_data.id, None) # Placeholder

        # Masukkan ke Canvas Frame (PENTING)
        item.setParentItem(self.canvas_frame)
        
        # Set Properties
        props = layer_data.properties
        item.start_time = float(props.get("start_time", 0.0))
        item.update_transform(props)
        item.setZValue(layer_data.z_index)

        # Sambungkan sinyal Item ke Panel (Relay ke Controller)
        # Sinyal Item: (str, dict) -> Sinyal Panel: (str, dict)
        item.sig_transform_changed.connect(self.sig_property_changed)

        self.items_map[layer_data.id] = item

    def on_layer_removed(self, lid):
        if lid in self.items_map:
            item = self.items_map[lid]
            item.sig_transform_changed.disconnect() # Putus sinyal
            self.scene.removeItem(item)
            del self.items_map[lid]

    def on_property_changed(self, layer_id, props):
        if layer_id in self.items_map:
            item = self.items_map[layer_id]
            
            # ✅ BLOCK SIGNAL agar tidak loop (Controller -> UI -> Controller)
            item.blockSignals(True) 
            item.update_transform(props)
            item.blockSignals(False)

    # ✅ [PERBAIKAN 1] Tambahkan method ini agar tidak AttributeError
    def on_selection_changed(self, layer_data):
        """Dipanggil oleh Binder saat seleksi berubah di Timeline"""
        self.scene.blockSignals(True) # Hindari ping-pong sinyal
        self.scene.clearSelection()
        
        # Binder mengirim objek LayerModel (layer_data) atau None
        if layer_data and hasattr(layer_data, 'id'):
            lid = layer_data.id
            if lid in self.items_map:
                self.items_map[lid].setSelected(True)
        
        self.scene.blockSignals(False)

    # --- INTERNAL INTERACTION ---
    
    def _on_internal_selection(self):
        """Saat user klik item di canvas -> Beritahu Controller"""
        items = self.scene.selectedItems()
        if items:
            item = items[0]
            if hasattr(item, 'layer_id'):
                self.sig_layer_selected.emit(item.layer_id)
        else:
            self.sig_layer_selected.emit(None)