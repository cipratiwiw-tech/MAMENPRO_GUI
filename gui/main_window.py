# gui/main_window.py
import sys
from PySide6.QtWidgets import QMainWindow, QSplitter
from PySide6.QtCore import Qt

# Import Panels
# Pastikan nama file dan class sesuai dengan folder kamu
from gui.center_panel.preview_panel import PreviewPanel
from gui.panels.layer_panel import LayerPanel
from gui.panels.media_panel import MediaPanel
from gui.right_panel.setting_panel import SettingPanel

class VideoEditorApp(QMainWindow):
    def __init__(self):  # <--- HAPUS 'controller' DARI SINI
        super().__init__()
        self.setWindowTitle("MAMENPRO EDITOR")
        self.resize(1280, 720)
        
        # 1. Init UI Components
        # Panel-panel ini juga TIDAK BOLEH terima controller lagi
        self.preview_panel = PreviewPanel()
        self.layer_panel = LayerPanel()
        self.media_panel = MediaPanel()   # <--- HAPUS controller
        self.setting_panel = SettingPanel() # <--- HAPUS controller
        
        # 2. Setup Layout
        self._init_layout()

    def _init_layout(self):
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Kiri: Layer & Media (bisa digabung tab atau split lagi)
        # Untuk simpelnya kita taruh LayerPanel dulu
        self.splitter.addWidget(self.layer_panel)
        
        # Tengah: Preview
        self.splitter.addWidget(self.preview_panel)
        
        # Kanan: Settings
        self.splitter.addWidget(self.setting_panel)
        
        self.setCentralWidget(self.splitter)
        self.splitter.setSizes([300, 800, 350])