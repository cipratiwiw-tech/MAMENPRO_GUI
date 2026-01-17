# gui/left_panel/background_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal
from gui.services.media_dialog_service import MediaDialogService

class BackgroundPanel(QWidget):
    # Signal: path
    sig_set_background = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl = QLabel("BACKGROUNDS")
        lbl.setStyleSheet("font-weight: bold; color: #e5c07b; margin-bottom: 10px;")
        layout.addWidget(lbl)

        # Import Button
        btn_import = QPushButton("📂 Import Background")
        btn_import.setStyleSheet("""
            QPushButton { 
                background-color: #e5c07b; color: #282c34; font-weight: bold; 
                padding: 10px; border-radius: 4px; 
            }
            QPushButton:hover { background-color: #f0d19e; }
        """)
        btn_import.clicked.connect(self._on_import_clicked)
        layout.addWidget(btn_import)
        
        lbl_info = QLabel("Tips: Layer ini akan otomatis ditaruh di paling bawah (Behind All).")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #5c6370; font-size: 11px; margin-top: 5px;")
        layout.addWidget(lbl_info)

        layout.addStretch()

    def _on_import_clicked(self):
        # Gunakan service untuk file dialog
        data = MediaDialogService.get_media_file(self)
        if data:
            self.sig_set_background.emit(data['path'])