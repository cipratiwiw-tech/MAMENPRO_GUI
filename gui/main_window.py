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
        # [UPGRADE 1] Ukuran Window Start lebih ideal untuk Video Editing (16:9 ratio)
        self.resize(1600, 900)
        
        if STYLESHEET:
            self.setStyleSheet(STYLESHEET)
        
        # 1. Init Components
        self.engine = PreviewEngine()
        self._init_ui()
        
        # 2. Init Controller (Menyerahkan logika ke Controller)
        self.controller = EditorController(self)
        
    def _init_ui(self):
        # Gunakan style sheet khusus untuk handle splitter agar terlihat modern
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(2) # Garis pembatas tipis elegan
        
        self.setCentralWidget(self.splitter)
        
        self.preview = PreviewPanel()
        self.layer_panel = LayerPanel()
        self.setting = SettingPanel()
        
        self.splitter.addWidget(self.layer_panel)
        self.splitter.addWidget(self.preview)
        self.splitter.addWidget(self.setting)
        
        # [UPGRADE 2] Distribusi Lebar Panel (Kiri, Tengah, Kanan)
        # Total +/- 1600px: Kiri 300, Tengah Dominan, Kanan 360 (biar ga kepotong)
        self.splitter.setSizes([300, 940, 360]) 
        
        # [UPGRADE 3] Stretch Factor (Logika Agar Center Tidak "Memakan" Sisi)
        # 0 = Fixed/Statis (tidak prioritas resize), 1 = Expand (mengisi sisa ruang)
        self.splitter.setStretchFactor(0, 0) # Kiri: Pertahankan ukuran
        self.splitter.setStretchFactor(1, 1) # Tengah: Isi ruang sisa
        self.splitter.setStretchFactor(2, 0) # Kanan: Pertahankan ukuran
        
        # Mencegah panel hilang total saat di-drag mentok
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(2, False)

        self.preview.scene.setSceneRect(0, 0, 1080, 1920)
        
    # --- [BARU] EVENT PENUTUPAN APLIKASI ---
    def closeEvent(self, event):
        """Dipanggil otomatis saat tombol X diklik"""
        print("[APP] Closing... Saving config.")
        if self.controller:
            self.controller.save_app_config()
        
        # Lanjutkan proses penutupan
        event.accept()

# Entry point tetap sama...
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoEditorApp()
    window.show()
    sys.exit(app.exec())