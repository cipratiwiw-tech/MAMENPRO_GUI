import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter
from PySide6.QtCore import Qt

# Import UI Components
from gui.center_panel.preview_panel import PreviewPanel
from gui.left_panel.layer_panel import LayerPanel
from gui.right_panel.setting_panel import SettingPanel
from engine.preview_engine import PreviewEngine 

# Import Controller
from gui.controllers.main_controller import EditorController

try:
    from gui.styles import STYLESHEET
except ImportError:
    STYLESHEET = ""

class VideoEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MamenPro_GUI")
        self.resize(1500, 768)
        
        if STYLESHEET:
            self.setStyleSheet(STYLESHEET)
        
        # 1. Init Components
        self.engine = PreviewEngine()
        self._init_ui()
        
        # 2. Init Controller (Menyerahkan logika ke Controller)
        # Kita passing 'self' agar controller bisa mengakses UI elements
        self.controller = EditorController(self)
        
    def _init_ui(self):
        self.splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.splitter)
        
        self.preview = PreviewPanel()
        self.layer_panel = LayerPanel()
        self.setting = SettingPanel()
        
        self.splitter.addWidget(self.layer_panel)
        self.splitter.addWidget(self.preview)
        self.splitter.addWidget(self.setting)
        
        self.splitter.setSizes([200, 800, 300])
        self.preview.scene.setSceneRect(0, 0, 1080, 1920) 

# Entry point tetap sama...
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoEditorApp()
    window.show()
    sys.exit(app.exec())