from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QLabel, QGraphicsScene, QPushButton, QSlider, QStyle, QGraphicsRectItem)
from PySide6.QtGui import QBrush, QPen, QColor, QPainter
from PySide6.QtCore import Qt, QTimer, Signal

# Import komponen terkait
from canvas.video_item import VideoItem
from gui.center_panel.video_view import VideoGraphicsView

class PreviewPanel(QWidget):
    sig_frame_selected = Signal(str)  # Kirim ID ke SettingPanel
    sig_item_moved = Signal(dict)     # Kirim Update Posisi X/Y saat drag

    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        self._init_ui()
        
        # Init Ukuran Awal (Delay sedikit agar UI siap)
        QTimer.singleShot(100, lambda: self.change_ratio(self.ratio_cb.currentText()))

    def _init_ui(self):
        # 1. Top Bar (Rasio & Zoom)
        top_bar = QHBoxLayout()
        self.ratio_cb = QComboBox()
        self.ratios = {
            "9:16 (TikTok)": (1080, 1920), 
            "16:9 (YouTube)": (1920, 1080),
            "1:1 (Square)": (1080, 1080), 
            "4:5 (IG Feed)": (1080, 1350)
        }
        self.ratio_cb.addItems(self.ratios.keys())
        self.ratio_cb.currentTextChanged.connect(self.change_ratio)
        
        top_bar.addWidget(QLabel("Ratio:"))
        top_bar.addWidget(self.ratio_cb)
        top_bar.addStretch()
        
        # 2. Area Preview
        self.scene = QGraphicsScene()
        # Set background scene jadi abu-abu gelap (area di luar canvas)
        self.scene.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        
        self.view = VideoGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # --- INIT GRAPHICS (CANVAS & GUIDE) ---
        self._init_graphics()
        
        # 3. Bottom Bar (Playback Controls)
        control_layout = QHBoxLayout()
        self.btn_play = QPushButton()
        self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        
        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setRange(0, 1000) # 0 - 100%
        
        control_layout.addWidget(self.btn_play)
        control_layout.addWidget(self.timeline_slider)
        
        # Add to Layout
        self.main_layout.addLayout(top_bar)
        self.main_layout.addWidget(self.view)
        self.main_layout.addLayout(control_layout)

        # Connections
        self.scene.selectionChanged.connect(self._on_selection)
        self.scene.changed.connect(self._on_changed)

    def _init_graphics(self):
        """Membuat area Canvas (Logic) dan Canvas Guide (Visual)"""
        
        # 1. Canvas LOGIC (Invisible Area untuk referensi ukuran & parent item jika perlu)
        # Ditaruh paling belakang (Z = -200)
        self.canvas = QGraphicsRectItem(0, 0, 1080, 1920)
        self.canvas.setBrush(Qt.NoBrush)
        self.canvas.setPen(Qt.NoPen) # Tidak terlihat
        self.canvas.setZValue(-200)  
        self.canvas.setFlag(QGraphicsRectItem.ItemIsMovable, False)
        self.canvas.setFlag(QGraphicsRectItem.ItemIsSelectable, False)
        self.scene.addItem(self.canvas)
        
        # 2. Canvas GUIDE (Garis Putus-putus Visual)
        # Ditaruh paling DEPAN (Z = 9999) agar selalu terlihat di atas video/background
        self.canvas_guide = QGraphicsRectItem(0, 0, 1080, 1920)
        self.canvas_guide.setBrush(Qt.NoBrush)
        
        # Garis Putih Putus-putus
        pen = QPen(QColor(255, 255, 255, 150), 4) # Sedikit lebih tebal
        pen.setStyle(Qt.DashLine)
        self.canvas_guide.setPen(pen)
        
        self.canvas_guide.setZValue(9999) 
        
        # Non-interaktif (Tembus pandang mouse)
        self.canvas_guide.setFlag(QGraphicsRectItem.ItemIsMovable, False)
        self.canvas_guide.setFlag(QGraphicsRectItem.ItemIsSelectable, False)
        self.canvas_guide.setAcceptedMouseButtons(Qt.NoButton) # Klik tembus ke bawah
        
        self.scene.addItem(self.canvas_guide)

    def change_ratio(self, name):
        w, h = self.ratios[name]
        
        # Update Logic & Guide (Safety Check)
        if hasattr(self, 'canvas'):
            self.canvas.setRect(0, 0, w, h)
            
        if hasattr(self, 'canvas_guide'):
            self.canvas_guide.setRect(0, 0, w, h)
            
        self.scene.setSceneRect(0, 0, w, h)
        
        # Reset View agar pas di tengah
        if hasattr(self, 'view'):
            self.view.resetTransform()
            if hasattr(self, 'canvas'):
                self.view.fitInView(self.canvas, Qt.KeepAspectRatio)
            self.view.scale(0.9, 0.9) # Sedikit padding
            if hasattr(self, 'canvas'):
                self.view.centerOn(self.canvas)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Pastikan atribut sudah ada sebelum dipanggil (Fix Error AttributeError)
        if hasattr(self, 'ratio_cb') and hasattr(self, 'canvas_guide'):
            self.change_ratio(self.ratio_cb.currentText())

    def select_frame_by_code(self, frame_code):
        self.scene.blockSignals(True)
        self.scene.clearSelection()
        
        found = False
        for item in self.scene.items():
            if hasattr(item, 'name') and item.name == frame_code:
                item.setSelected(True)
                found = True
                break
        
        self.scene.blockSignals(False)
        if found:
            self._on_selection() # Trigger manual update UI

    def _on_selection(self):
        sel = self.scene.selectedItems()
        if sel and isinstance(sel[0], VideoItem):
            self.sig_frame_selected.emit(sel[0].name)

    def _on_changed(self, region):
        # Saat item digeser mouse, kirim sinyal update ke panel kanan
        sel = self.scene.selectedItems()
        if sel and isinstance(sel[0], VideoItem):
            self.sig_item_moved.emit(sel[0].settings)