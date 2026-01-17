# gui/panels/media_panel.py
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from gui.services.media_dialog_service import MediaDialogService

class MediaPanel(QWidget):
    # Signal: type, path
    sig_request_import = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        lbl = QLabel("MEDIA LIBRARY")
        lbl.setStyleSheet("font-weight: bold; color: #56b6c2;")
        layout.addWidget(lbl)

        # Import Button
        btn = QPushButton("📂 Import File")
        btn.setStyleSheet("""
            QPushButton { background-color: #3a0ca3; padding: 10px; border-radius: 4px; color: white; font-weight: bold;}
            QPushButton:hover { background-color: #4361ee; }
        """)
        btn.clicked.connect(self._on_import_clicked)
        layout.addWidget(btn)
        
        layout.addStretch()

    def _on_import_clicked(self):
        # 1. Panggil Service (UI Helper)
        data = MediaDialogService.get_media_file(self)
        
        # 2. Jika ada hasil, Emit Signal (Hanya meneruskan data)
        if data:
            self.sig_request_import.emit(data['type'], data['path'])