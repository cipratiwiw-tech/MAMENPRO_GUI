# gui/main_window.py
import sys
from PySide6.QtWidgets import QMainWindow, QSplitter, QTabWidget, QStatusBar, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

# Import Panels (Sama seperti sebelumnya)
from gui.center_panel.preview_panel import PreviewPanel
from gui.panels.layer_panel import LayerPanel
from gui.panels.media_panel import MediaPanel
from gui.right_panel.setting_panel import SettingPanel
from gui.panels.text_panel import TextPanel
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
        self.render_tab = RenderTab()
        self.template_tab = TemplateTab()
        
        self.setting_panel = SettingPanel()
        self.text_panel = TextPanel()
        
        # [BARU] Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # 2. Setup Layout & Menu
        self._init_layout()
        self._init_menu()

    def _init_layout(self):
        # ... (Layout Code SAMA PERSIS dengan sebelumnya) ...
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Kiri
        left_tabs = QTabWidget()
        left_tabs.addTab(self.layer_panel, "Layers")
        left_tabs.addTab(self.media_panel, "Media")
        left_tabs.addTab(self.template_tab, "Templates")
        left_tabs.addTab(self.render_tab, "Export")
        main_splitter.addWidget(left_tabs)
        
        # Tengah
        main_splitter.addWidget(self.preview_panel)
        
        # Kanan
        self.right_tabs = QTabWidget()
        self.right_tabs.addTab(self.setting_panel, "Transform")
        self.right_tabs.addTab(self.text_panel, "Text Style")
        main_splitter.addWidget(self.right_tabs)
        
        main_splitter.setSizes([350, 750, 350])
        self.setCentralWidget(main_splitter)

    def _init_menu(self):
        # [BARU] Membuat Menu Bar File
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        
        # Action Open
        self.action_open = QAction("Open Project", self)
        file_menu.addAction(self.action_open)
        
        # Action Save
        self.action_save = QAction("Save Project", self)
        file_menu.addAction(self.action_save)
        
        file_menu.addSeparator()
        
        # Action Exit
        action_exit = QAction("Exit", self)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)