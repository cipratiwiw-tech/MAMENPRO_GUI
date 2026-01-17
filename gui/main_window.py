import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter
from PySide6.QtCore import Qt

from gui.center_panel.preview_panel import PreviewPanel
from gui.panels.layer_panel import LayerPanel
from gui.panels.media_panel import MediaPanel
from gui.panels.text_panel import TextTab
from gui.right_panel.setting_panel import SettingPanel

from canvas.video_item import VideoItem
from manager.editor_controller import EditorController
from gui.center_panel.preview_panel import PreviewPanel


try:
    from gui.styles import STYLESHEET
except ImportError:
    STYLESHEET = ""

class VideoEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.preview_panel = PreviewPanel()

        # ⛔ PAKSA JADI SATU-SATUNYA WIDGET
        self.setCentralWidget(self.preview_panel)

        self.setWindowTitle("PREVIEW TEST")
        self.resize(800, 600)

 

    def _init_ui(self):
        # Gunakan style sheet khusus untuk handle splitter agar terlihat modern
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(2) # Garis pembatas tipis elegan
        
        self.setCentralWidget(self.splitter)
        
        center_panel = self.preview_panel

        self.layer_panel = LayerPanel()
        self.setting = SettingPanel(self.controller)
        self.media_tab = MediaPanel(self.controller)
        center_panel = self.preview_panel


        
        self.splitter.addWidget(self.layer_panel)
        self.splitter.addWidget(center_panel)
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

        self.preview_panel.scene.setSceneRect(0, 0, 1080, 1920)

        
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