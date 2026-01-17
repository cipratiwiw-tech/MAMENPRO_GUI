# gui/main_window.py
import sys
from PySide6.QtWidgets import QMainWindow, QSplitter
from PySide6.QtCore import Qt

# Import Panels
from gui.center_panel.preview_panel import PreviewPanel
from gui.panels.layer_panel import LayerPanel
from gui.panels.media_panel import MediaPanel
from gui.right_panel.setting_panel import SettingPanel

class VideoEditorApp(QMainWindow):
    def __init__(self, controller): 
        # Controller dipass hanya agar panel anak (seperti MediaPanel) 
        # yang MEMANG butuh akses langsung untuk aksi bisa mendapatkannya.
        # TAPI MainWindow sendiri TIDAK BOLEH menggunakannya untuk logic.
        super().__init__()
        self.setWindowTitle("MAMENPRO EDITOR - CLEAN ARCHITECTURE")
        self.resize(1280, 720)
        
        # 1. Init UI Components
        # Perhatikan: Tidak ada wiring signal di sini!
        self.preview_panel = PreviewPanel()
        self.layer_panel = LayerPanel()
        self.media_panel = MediaPanel()
        self.setting_panel = SettingPanel(controller) 
        
        # 2. Setup Layout
        self._init_layout()
        
        # HAPUS _connect_signals()! 
        # HAPUS logic lambda!
        
        # Registrasi Preview ke Controller (opsional, jika pakai pola wiring Controller->Preview langsung)
        # Tapi sebaiknya wiring ini juga dipindah ke Binder jika ingin purist.
        # Untuk saat ini, biarkan Controller-Preview connect via Binder di langkah Main.

    def _init_layout(self):
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Kiri
        self.splitter.addWidget(self.layer_panel)
        
        # Tengah
        self.splitter.addWidget(self.preview_panel)
        
        # Kanan
        self.splitter.addWidget(self.setting_panel)
        
        self.setCentralWidget(self.splitter)
        self.splitter.setSizes([300, 800, 350])

    # Method closeEvent boleh memanggil save config controller jika diperlukan, 
    # atau dipindah ke Binder juga (lebih baik).