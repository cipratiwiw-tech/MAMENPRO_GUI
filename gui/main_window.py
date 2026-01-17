# [source_code_start:gui/main_window.py]
# gui/main_window.py
import sys
from PySide6.QtWidgets import (QMainWindow, QSplitter, QTabWidget, QStatusBar, 
                             QWidget, QVBoxLayout)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt

# Import Panels
from gui.center_panel.preview_panel import PreviewPanel
from gui.panels.layer_panel import LayerPanel
from gui.panels.media_panel import MediaPanel
from gui.right_panel.setting_panel import SettingPanel
from gui.panels.text_panel import TextPanel
from gui.left_panel.render_tab import RenderTab
from gui.left_panel.template_tab import TemplateTab
from gui.left_panel.audio_tab import AudioTab
from gui.left_panel.presetchroma_panel import PresetChromaPanel
from gui.panels.caption_panel import CaptionPanel

class VideoEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MAMENPRO EDITOR")
        self.resize(1366, 850) # Sedikit lebih tinggi
        
        # 1. Init UI Components
        # ---------------------------------------------------
        # CENTER (PREVIEW)
        self.preview_panel = PreviewPanel()
        
        # BOTTOM (TIMELINE & RENDER)
        self.layer_panel = LayerPanel()
        self.render_tab = RenderTab() # Pindah ke bawah
        
        # LEFT (ASSETS)
        self.media_panel = MediaPanel()
        self.template_tab = TemplateTab()
        self.audio_tab = AudioTab()
        self.caption_panel = CaptionPanel()
        self.chroma_panel = PresetChromaPanel()
        
        # RIGHT (PROPERTIES)
        self.setting_panel = SettingPanel()
        self.text_panel = TextPanel()
        
        # STATUS BAR
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # 2. Setup Layout & Menu
        self._init_layout()
        self._init_menu()

    def _init_layout(self):
        """
        Layout Hierarchy:
        ROOT (VBox)
          └── Vertical Splitter
               ├── TOP AREA (Horizontal Splitter)
               │    ├── LEFT: Assets
               │    ├── CENTER: Preview
               │    └── RIGHT: Properties
               └── BOTTOM AREA (Horizontal Splitter) [BARU]
                    ├── LEFT: Timeline (90%)
                    └── RIGHT: Export (10%)
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. SPLITTER UTAMA (ATAS vs BAWAH)
        vertical_splitter = QSplitter(Qt.Vertical)
        
        # ==================================================
        # A. TOP AREA
        # ==================================================
        top_splitter = QSplitter(Qt.Horizontal)
        
        # A.1 LEFT TABS (Assets Only - Render Removed)
        self.left_tabs = QTabWidget()
        self.left_tabs.addTab(self.media_panel, "Media")
        self.left_tabs.addTab(self.template_tab, "Templates")
        self.left_tabs.addTab(self.audio_tab, "Audio")
        self.left_tabs.addTab(self.caption_panel, "CC / AI")
        self.left_tabs.addTab(self.chroma_panel, "FX / Chroma")
        
        # A.2 CENTER (Preview)
        # self.preview_panel
        
        # A.3 RIGHT TABS (Properties)
        self.right_tabs = QTabWidget()
        self.right_tabs.addTab(self.setting_panel, "Transform")
        self.right_tabs.addTab(self.text_panel, "Text Style")
        
        top_splitter.addWidget(self.left_tabs)
        top_splitter.addWidget(self.preview_panel)
        top_splitter.addWidget(self.right_tabs)
        
        # Rasio Top (Kiri:Kecil, Tengah:Besar, Kanan:Kecil)
        top_splitter.setSizes([280, 800, 280])
        top_splitter.setCollapsible(0, True)
        top_splitter.setCollapsible(2, True)

        # ==================================================
        # B. BOTTOM AREA (Timeline + Render) [MODIFIKASI]
        # ==================================================
        bottom_splitter = QSplitter(Qt.Horizontal)
        
        # B.1 Timeline (Kiri - Lebar)
        bottom_splitter.addWidget(self.layer_panel)
        
        # B.2 Render (Kanan - Sempit)
        # Kita bungkus RenderTab dalam QTabWidget agar rapi sejajar Timeline
        self.bottom_right_tabs = QTabWidget()
        self.bottom_right_tabs.addTab(self.render_tab, "🚀 EXPORT")
        bottom_splitter.addWidget(self.bottom_right_tabs)
        
        # Rasio Bottom (Timeline: 90%, Render: 10%)
        # Angka dalam pixel, Qt akan menghitung persentasenya
        bottom_splitter.setSizes([1200, 150]) 
        bottom_splitter.setCollapsible(1, True) # Panel Render bisa ditutup
        
        # ==================================================
        # C. FINAL ASSEMBLY
        # ==================================================
        vertical_splitter.addWidget(top_splitter)
        vertical_splitter.addWidget(bottom_splitter)
        vertical_splitter.setSizes([600, 250]) # Tinggi Atas vs Bawah
        
        root_layout.addWidget(vertical_splitter)

    def _init_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        
        self.action_open = QAction("Open Project", self)
        file_menu.addAction(self.action_open)
        
        self.action_save = QAction("Save Project", self)
        file_menu.addAction(self.action_save)
        
        file_menu.addSeparator()
        
        action_exit = QAction("Exit", self)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)
        
        self.action_play = QAction("Play/Pause", self)
        self.action_play.setShortcut(QKeySequence(Qt.Key_Space))
        self.addAction(self.action_play)
# [source_code_end]