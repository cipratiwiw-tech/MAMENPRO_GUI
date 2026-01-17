
# gui/main_window.py
import sys
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QSplitter,
    QTabWidget,
    QStatusBar,
    QVBoxLayout,
    QHBoxLayout,
    QFrame
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt

# ==================================================
# IMPORT PANELS
# ==================================================
from gui.center_panel.preview_panel import PreviewPanel
from gui.panels.layer_panel import LayerPanel
from gui.right_panel.setting_panel import SettingPanel

# LEFT PANELS (ALL TABS)
from gui.panels.media_panel import MediaPanel
from gui.left_panel.text_panel import TextPanel
from gui.left_panel.background_panel import BackgroundPanel
from gui.left_panel.template_tab import TemplateTab
from gui.left_panel.graphics_panel import GraphicsPanel
from gui.left_panel.presetchroma_panel import PresetChromaPanel
from gui.left_panel.audio_tab import AudioTab
from gui.left_panel.utilities_panel import UtilitiesPanel
from gui.left_panel.render_tab import RenderTab # Dipindah ke Kiri

class VideoEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MAMENPRO EDITOR")
        self.resize(1600, 900)

        # ===============================
        # INIT PANELS
        # ===============================
        # CENTER
        self.preview_panel = PreviewPanel()

        # TIMELINE
        self.layer_panel = LayerPanel()

        # LEFT PANELS
        self.media_panel = MediaPanel()
        self.text_panel = TextPanel()
        self.bg_panel = BackgroundPanel()
        self.template_tab = TemplateTab()
        self.graphics_panel = GraphicsPanel()
        self.chroma_panel = PresetChromaPanel()
        self.audio_tab = AudioTab()
        self.util_panel = UtilitiesPanel()
        
        # EXPORT PANEL (Moved to Left)
        self.render_tab = RenderTab()

        # RIGHT (PROPERTIES ONLY)
        self.setting_panel = SettingPanel()
        
        # STATUS BAR
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self._init_layout()
        self._init_menu()

    # ==================================================
    # LAYOUT
    # ==================================================
    def _init_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ==================================================
        # LEFT + CENTER CONTAINER
        # ==================================================
        left_center_container = QWidget()
        left_center_layout = QVBoxLayout(left_center_container)
        left_center_layout.setContentsMargins(0, 0, 0, 0)
        left_center_layout.setSpacing(0)

        # -------------------------------
        # TOP AREA: SPLITTER (LEFT TABS | CENTER AREA)
        # -------------------------------
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.setHandleWidth(1)

        # LEFT TABS (SIDEBAR STYLE)
        self.left_tabs = QTabWidget()
        self.left_tabs.setTabPosition(QTabWidget.West) # TAB DI KIRI
        self.left_tabs.setStyleSheet("""
            QTabBar::tab { 
                height: 50px; width: 50px; 
                padding: 0px; margin: 0px;
                border: none;
                background: #23272e;
                color: #9da5b4;
            }
            QTabBar::tab:selected { 
                background: #2c313a; 
                border-left: 3px solid #61afef;
                color: #dcdcdc;
            }
            QTabBar::tab:hover {
                background: #282c34;
                color: #ffffff;
            }
            QTabWidget::pane { border: none; background: #2c313a; }
        """)

        # 1. Media
        self.left_tabs.addTab(self.media_panel, "📁")
        self.left_tabs.setTabToolTip(0, "Media")
        
        # 2. Text
        self.left_tabs.addTab(self.text_panel, "T")
        self.left_tabs.setTabToolTip(1, "Text")
        
        # 3. Background
        self.left_tabs.addTab(self.bg_panel, "BG")
        self.left_tabs.setTabToolTip(2, "Background")
        
        # 4. Templates
        self.left_tabs.addTab(self.template_tab, "田")
        self.left_tabs.setTabToolTip(3, "Templates")
        
        # 5. Graphics
        self.left_tabs.addTab(self.graphics_panel, "★")
        self.left_tabs.setTabToolTip(4, "Graphics")
        
        # 6. Effects
        self.left_tabs.addTab(self.chroma_panel, "FX")
        self.left_tabs.setTabToolTip(5, "Effects")
        
        # 7. Audio
        self.left_tabs.addTab(self.audio_tab, "♪")
        self.left_tabs.setTabToolTip(6, "Audio")
        
        # 8. Utilities
        self.left_tabs.addTab(self.util_panel, "🛠")
        self.left_tabs.setTabToolTip(7, "Utilities")
        
        # Container Tab Kiri
        left_container = QWidget()
        left_layout_inner = QVBoxLayout(left_container)
        left_layout_inner.setContentsMargins(0,0,0,0)
        left_layout_inner.addWidget(self.left_tabs)
        left_container.setMinimumWidth(340) # Sedikit diperlebar untuk Export settings

        # B. CENTER AREA (RENDER TOOLBAR + PREVIEW) -> INI YANG BARU
        center_area_widget = QWidget()
        center_layout = QVBoxLayout(center_area_widget)
        center_layout.setContentsMargins(0,0,0,0)
        center_layout.setSpacing(0)

        # [1] Render Toolbar (Ditaruh diatas)
        center_layout.addWidget(self.render_tab) 
        
        # [2] Preview Panel (Dibawahnya)
        center_layout.addWidget(self.preview_panel)

        # Masukkan ke Splitter
        top_splitter.addWidget(left_container)
        top_splitter.addWidget(center_area_widget) # Ganti self.preview_panel dg container baru

        top_splitter.setStretchFactor(0, 1)
        top_splitter.setStretchFactor(1, 4)
        top_splitter.setSizes([340, 1200])

        # -------------------------------
        # TIMELINE
        # -------------------------------
        # self.layer_panel.setMinimumHeight(180)
        # self.layer_panel.setMaximumHeight(300)

        left_center_layout.addWidget(top_splitter)
        left_center_layout.addWidget(self.layer_panel)

        # ==================================================
        # RIGHT PANEL (PROPERTIES ONLY)
        # ==================================================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0) # Rapat tepi
        right_layout.setSpacing(0)

        # ---- PROPERTIES TABS (FULL HEIGHT)
        self.right_tabs = QTabWidget()
        self.right_tabs.setStyleSheet("QTabWidget::pane { border-top: 2px solid #21252b; }")
        self.right_tabs.addTab(self.setting_panel, "Properties")
      
        right_layout.addWidget(self.right_tabs)

        right_panel.setMinimumWidth(300)
        right_panel.setMaximumWidth(380)

        # ==================================================
        # FINAL ASSEMBLY
        # ==================================================
        root_layout.addWidget(left_center_container, 1)
        root_layout.addWidget(right_panel, 0)

    # ==================================================
    # MENU (Tidak Berubah)
    # ==================================================
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

        # PLAY / PAUSE
        self.action_play = QAction("Play / Pause", self)
        self.action_play.setShortcut(QKeySequence(Qt.Key_Space))
        self.addAction(self.action_play)
