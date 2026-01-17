# gui/main_window.py
import sys
from PySide6.QtWidgets import QMainWindow, QSplitter, QTabWidget
from PySide6.QtCore import Qt

# Import Semua Panel
from gui.center_panel.preview_panel import PreviewPanel
from gui.panels.layer_panel import LayerPanel
from gui.panels.media_panel import MediaPanel
from gui.right_panel.setting_panel import SettingPanel
from gui.panels.text_panel import TextPanel
# [BARU] Import Tab Kiri Tambahan
from gui.left_panel.render_tab import RenderTab
from gui.left_panel.template_tab import TemplateTab

class VideoEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MAMENPRO EDITOR")
        self.resize(1366, 768)
        
        # 1. Init UI Components
        self.preview_panel = PreviewPanel()
        self.layer_panel = LayerPanel()
        self.media_panel = MediaPanel()
        # [BARU]
        self.render_tab = RenderTab()
        self.template_tab = TemplateTab()
        
        self.setting_panel = SettingPanel()
        self.text_panel = TextPanel()
        
        # 2. Setup Layout
        self._init_layout()

    def _init_layout(self):
        main_splitter = QSplitter(Qt.Horizontal)
        
        # --- KIRI (Media, Layers, Templates, Render) ---
        left_tabs = QTabWidget()
        left_tabs.addTab(self.layer_panel, "Layers")
        left_tabs.addTab(self.media_panel, "Media")
        left_tabs.addTab(self.template_tab, "Templates") # [BARU]
        left_tabs.addTab(self.render_tab, "Export")      # [BARU]
        main_splitter.addWidget(left_tabs)
        
        # --- TENGAH (Preview) ---
        main_splitter.addWidget(self.preview_panel)
        
        # --- KANAN (Properties) ---
        self.right_tabs = QTabWidget()
        self.right_tabs.addTab(self.setting_panel, "Transform")
        self.right_tabs.addTab(self.text_panel, "Text Style")
        main_splitter.addWidget(self.right_tabs)
        
        main_splitter.setSizes([350, 750, 350])
        self.setCentralWidget(main_splitter)