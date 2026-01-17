# gui/left_panel/audio_tab.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QPushButton, QLabel, QHBoxLayout)
from PySide6.QtCore import Signal, Qt
from gui.services.media_dialog_service import MediaDialogService

class AudioTab(QWidget):
    # SIGNAL OUT: Request tambah layer audio (path)
    sig_request_add_audio = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl = QLabel("AUDIO LIBRARY")
        lbl.setStyleSheet("font-weight: bold; color: #e5c07b; margin-bottom: 5px;")
        layout.addWidget(lbl)

        # List Mock Audio (Bisa diganti scan folder asset nanti)
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("border: 1px solid #3e4451;")
        
        mock_audios = [
            ("🎵 Happy Background", "assets/audio/happy.mp3"),
            ("🎵 Dramatic Effect", "assets/audio/drama.mp3"),
            ("🎵 Pop Beat", "assets/audio/pop.mp3")
        ]
        
        for name, path in mock_audios:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, path)
            self.list_widget.addItem(item)
            
        self.list_widget.itemDoubleClicked.connect(self._on_item_dbl_clicked)
        layout.addWidget(self.list_widget)

        # Import Button
        self.btn_import = QPushButton("📂 Import Audio")
        self.btn_import.setStyleSheet("""
            QPushButton { background-color: #e5c07b; color: black; font-weight: bold; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #f0d19e; }
        """)
        self.btn_import.clicked.connect(self._on_import_clicked)
        layout.addWidget(self.btn_import)

    def _on_item_dbl_clicked(self, item):
        path = item.data(Qt.UserRole)
        # Emit path, biarkan Controller yang memutuskan cara load-nya
        self.sig_request_add_audio.emit(path)

    def _on_import_clicked(self):
        # Gunakan Service yang sudah ada (perlu sedikit modifikasi service untuk support audio filter kalau mau strict)
        # Untuk sekarang kita pakai filter default dulu atau update service nanti
        # Kita asumsikan Service bisa handle atau kita tambah method get_audio_file nanti
        # Disini kita pakai QFileDialog langsung via Service logic kalau sudah diupdate, 
        # atau emit request import umum.
        
        # Demi strictness "Panel jangan logika", kita delegasikan ke Dialog Service
        # (Kita akan update MediaDialogService sedikit di bawah untuk support Audio)
        path = MediaDialogService.get_audio_file(self) 
        if path:
            self.sig_request_add_audio.emit(path)