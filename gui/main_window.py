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
        self.resize(1600, 900)

        # ===============================
        # INIT PANELS
        # ===============================
        # CENTER
        self.preview_panel = PreviewPanel()

        # TIMELINE
        self.layer_panel = LayerPanel()

        # LEFT (ASSETS)
        self.media_panel = MediaPanel()
        self.template_tab = TemplateTab()
        self.audio_tab = AudioTab()
        self.caption_panel = CaptionPanel()
        self.chroma_panel = PresetChromaPanel()

        # RIGHT (PROPERTIES)
        self.setting_panel = SettingPanel()
        self.text_panel = TextPanel()
        self.render_tab = RenderTab()  # 🔥 SELALU TERLIHAT

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

        # ROOT: HORIZONTAL
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ==================================================
        # LEFT + CENTER (VERTICAL)
        # ==================================================
        left_center_container = QWidget()
        left_center_layout = QVBoxLayout(left_center_container)
        left_center_layout.setContentsMargins(0, 0, 0, 0)
        left_center_layout.setSpacing(0)

        # -------------------------------
        # TOP: ASSETS + PREVIEW
        # -------------------------------
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.setHandleWidth(1)

        # LEFT TABS (ASSETS)
        self.left_tabs = QTabWidget()
        self.left_tabs.addTab(self.media_panel, "Media")
        self.left_tabs.addTab(self.template_tab, "Tpl")
        self.left_tabs.addTab(self.audio_tab, "Audio")
        self.left_tabs.addTab(self.caption_panel, "CC")
        self.left_tabs.addTab(self.chroma_panel, "FX")

        # ADD TOP WIDGETS
        top_splitter.addWidget(self.left_tabs)
        top_splitter.addWidget(self.preview_panel)

        top_splitter.setStretchFactor(0, 1)
        top_splitter.setStretchFactor(1, 5)
        top_splitter.setSizes([280, 1200])

        # -------------------------------
        # TIMELINE (ONLY LEFT + CENTER)
        # -------------------------------
        self.layer_panel.setMinimumHeight(160)
        self.layer_panel.setMaximumHeight(260)

        left_center_layout.addWidget(top_splitter)
        left_center_layout.addWidget(self.layer_panel)

        # ==================================================
        # RIGHT PANEL (FULL HEIGHT)
        # ==================================================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(6)

        # ---- PROPERTIES TABS
        self.right_tabs = QTabWidget()
        self.right_tabs.addTab(self.setting_panel, "Transform")
        self.right_tabs.addTab(self.text_panel, "Style")

        right_layout.addWidget(self.right_tabs, 1)

        # ---- SEPARATOR
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        right_layout.addWidget(separator)

        # ---- RENDER (ALWAYS VISIBLE)
        self.render_tab.setMinimumHeight(220)
        self.render_tab.setMaximumHeight(300)
        right_layout.addWidget(self.render_tab, 0)

        right_panel.setMinimumWidth(300)
        right_panel.setMaximumWidth(360)

        # ==================================================
        # FINAL ASSEMBLY
        # ==================================================
        root_layout.addWidget(left_center_container, 1)
        root_layout.addWidget(right_panel, 0)

    # ==================================================
    # MENU
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
