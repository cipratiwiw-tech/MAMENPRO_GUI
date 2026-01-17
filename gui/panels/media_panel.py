# gui/panels/media_panel.py
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PySide6.QtCore import Signal
from gui.services.media_dialog_service import MediaDialogService

class MediaPanel(QWidget):
    # Sinyal keluar: (tipe_layer, path_file)
    sig_request_import = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI Setup
        self.btn_import = QPushButton("📂 Import Media")
        self.btn_import.setStyleSheet("""
            QPushButton { background-color: #3a0ca3; color: white; padding: 10px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #4361ee; }
        """)
        self.btn_import.clicked.connect(self._on_import_clicked)

        layout = QVBoxLayout(self)
        layout.addWidget(self.btn_import)
        layout.addStretch()

    def _on_import_clicked(self):
        # 1. Panggil Service untuk buka dialog (UI Logic)
        result = MediaDialogService.open_import_dialog(self)
        
        # 2. Jika user pilih file, lempar Sinyal (Event)
        if result:
            # Kirim 'video'/'image' dan path ke Binder
            self.sig_request_import.emit(result['type'], result['path'])