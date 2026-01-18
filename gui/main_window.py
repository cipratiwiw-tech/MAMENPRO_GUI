# gui/main_window.py
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QTabWidget, QStatusBar,
    QVBoxLayout, QHBoxLayout, QFrame
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt

# IMPORT PANELS
from gui.center_panel.preview_panel import PreviewPanel
from gui.panels.layer_panel import LayerPanel
from gui.right_panel.setting_panel import SettingPanel

# LEFT PANELS
from gui.left_panel.assets_panel import AssetsPanel
from gui.left_panel.template_tab import TemplateTab
from gui.left_panel.graphics_panel import GraphicsPanel
from gui.left_panel.presetchroma_panel import PresetChromaPanel
from gui.left_panel.audio_tab import AudioTab
from gui.left_panel.utilities_panel import UtilitiesPanel
from gui.left_panel.render_tab import RenderTab

class VideoEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MAMENPRO EDITOR")
        self.resize(1600, 900)

        # INIT PANELS
        self.preview_panel = PreviewPanel()
        self.layer_panel = LayerPanel()

        # LEFT PANELS
        self.assets_panel = AssetsPanel()
        self.template_tab = TemplateTab()
        self.graphics_panel = GraphicsPanel()
        self.chroma_panel = PresetChromaPanel()
        self.audio_tab = AudioTab()
        self.util_panel = UtilitiesPanel()
        
        self.render_tab = RenderTab()
        self.setting_panel = SettingPanel()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self._init_layout()
        self._init_menu()

    def _init_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout utama hanya untuk menampung Splitter Root
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Style khusus agar Handle (Garis Batas) terlihat dan enak digeser
        splitter_style = """
            QSplitter::handle {
                background-color: #181a1f;
            }
            QSplitter::handle:horizontal {
                width: 4px;
            }
            QSplitter::handle:vertical {
                height: 4px;
            }
            QSplitter::handle:hover {
                background-color: #56b6c2; /* Warna Cyan saat hover */
            }
        """

        # ==================================================
        # 1. ROOT SPLITTER (Horizontal)
        # Membagi: [Area Kerja Utama] || [Panel Properti Kanan]
        # ==================================================
        self.root_splitter = QSplitter(Qt.Horizontal)
        self.root_splitter.setHandleWidth(4)
        self.root_splitter.setStyleSheet(splitter_style)
        main_layout.addWidget(self.root_splitter)

        # ==================================================
        # 2. WORKSPACE SPLITTER (Vertical)
        # Membagi: [Atas (Kiri+Preview)] 
        #          =====================
        #          [Bawah (Timeline)]
        # ==================================================
        self.workspace_splitter = QSplitter(Qt.Vertical)
        self.workspace_splitter.setHandleWidth(4)
        self.workspace_splitter.setStyleSheet(splitter_style)

        # ==================================================
        # 3. TOP SPLITTER (Horizontal)
        # Membagi: [Panel Aset Kiri] || [Preview Tengah]
        # ==================================================
        self.top_splitter = QSplitter(Qt.Horizontal)
        self.top_splitter.setHandleWidth(4)
        self.top_splitter.setStyleSheet(splitter_style)

        # --- ISI TOP SPLITTER (KIRI & TENGAH) ---
        
        # A. LEFT TABS CONTAINER
        self.left_tabs = QTabWidget()
        self.left_tabs.setTabPosition(QTabWidget.West)
        self.left_tabs.setStyleSheet("""
            QTabBar::tab { 
                height: 50px; width: 50px; padding: 0px; margin: 0px;
                border: none; background: #23272e; color: #9da5b4;
            }
            QTabBar::tab:selected { 
                background: #2c313a; border-left: 3px solid #61afef; color: #dcdcdc;
            }
            QTabBar::tab:hover { background: #282c34; color: #ffffff; }
            QTabWidget::pane { border: none; background: #2c313a; }
        """)
        
        # Add Tabs (Sesuai urutan baru)
        self.left_tabs.addTab(self.assets_panel, "📂")
        self.left_tabs.setTabToolTip(0, "Quick Assets")
        self.left_tabs.addTab(self.template_tab, "田")
        self.left_tabs.setTabToolTip(1, "Templates")
        self.left_tabs.addTab(self.graphics_panel, "★")
        self.left_tabs.setTabToolTip(2, "Graphics")
        self.left_tabs.addTab(self.chroma_panel, "FX")
        self.left_tabs.setTabToolTip(3, "Effects")
        self.left_tabs.addTab(self.audio_tab, "♪")
        self.left_tabs.setTabToolTip(4, "Audio")
        self.left_tabs.addTab(self.util_panel, "🛠")
        self.left_tabs.setTabToolTip(5, "Utilities")

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.addWidget(self.left_tabs)
        left_container.setMinimumWidth(300) # Batas minimum lebar panel kiri

        # B. CENTER CONTAINER (Render Toolbar + Preview)
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0,0,0,0)
        center_layout.setSpacing(0)
        center_layout.addWidget(self.render_tab)
        center_layout.addWidget(self.preview_panel)
        center_container.setMinimumWidth(400) # Batas minimum lebar preview

        # Masukkan ke Top Splitter
        self.top_splitter.addWidget(left_container)
        self.top_splitter.addWidget(center_container)
        # Ratio Awal (Kiri : Tengah = 1 : 4)
        self.top_splitter.setStretchFactor(0, 1)
        self.top_splitter.setStretchFactor(1, 4)
        self.top_splitter.setSizes([350, 1000])

        # --- ISI WORKSPACE SPLITTER (ATAS & BAWAH) ---
        
        self.workspace_splitter.addWidget(self.top_splitter)
        self.workspace_splitter.addWidget(self.layer_panel)
        # Ratio Awal (Atas : Timeline = 3 : 1)
        self.workspace_splitter.setStretchFactor(0, 3)
        self.workspace_splitter.setStretchFactor(1, 1)
        self.workspace_splitter.setSizes([700, 250])

        # --- ISI ROOT SPLITTER (WORKSPACE & KANAN) ---
        
        # A. Workspace (Gabungan Kiri, Tengah, Bawah)
        self.root_splitter.addWidget(self.workspace_splitter)

        # B. Right Panel (Properties)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0,0,0,0)
        
        self.right_tabs = QTabWidget()
        self.right_tabs.setStyleSheet("QTabWidget::pane { border-top: 2px solid #21252b; }")
        self.right_tabs.addTab(self.setting_panel, "Properties")
        
        right_layout.addWidget(self.right_tabs)
        right_container.setMinimumWidth(280) # Batas minimum panel kanan
        
        self.root_splitter.addWidget(right_container)
        # Ratio Awal (Workspace : Properties = 5 : 1)
        self.root_splitter.setStretchFactor(0, 5)
        self.root_splitter.setStretchFactor(1, 1)
        self.root_splitter.setSizes([1300, 350])

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

        self.action_play = QAction("Play / Pause", self)
        self.action_play.setShortcut(QKeySequence(Qt.Key_Space))
        self.addAction(self.action_play)