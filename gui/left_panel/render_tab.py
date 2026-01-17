# gui/left_panel/render_tab.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QLineEdit, QComboBox, QFormLayout, QHBoxLayout)
from PySide6.QtCore import Signal
from gui.services.media_dialog_service import MediaDialogService

class RenderTab(QWidget):
    # Signal: Mengirim dict berisi konfigurasi render ke Logic
    sig_request_render = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        lbl = QLabel("EXPORT SETTINGS")
        lbl.setStyleSheet("font-weight: bold; color: #e06c75; margin-bottom: 10px;")
        layout.addWidget(lbl)

        # Form Layout
        form = QFormLayout()
        
        # 1. Output Path
        self.txt_path = QLineEdit("output.mp4")
        self.btn_browse = QPushButton("...")
        self.btn_browse.setFixedWidth(30)
        self.btn_browse.clicked.connect(self._on_browse_clicked)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.txt_path)
        path_layout.addWidget(self.btn_browse)
        form.addRow("File:", path_layout)

        # 2. Resolution
        self.combo_res = QComboBox()
        self.combo_res.addItems(["1920x1080 (FHD)", "1280x720 (HD)", "1080x1920 (TikTok)"])
        form.addRow("Resolution:", self.combo_res)

        # 3. FPS
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["30 FPS", "60 FPS", "24 FPS"])
        form.addRow("Frame Rate:", self.combo_fps)

        layout.addLayout(form)
        layout.addStretch()

        # Action Button
        self.btn_render = QPushButton("🚀 START RENDER")
        self.btn_render.setStyleSheet("""
            QPushButton { background-color: #e06c75; color: white; font-weight: bold; padding: 15px; border-radius: 5px; }
            QPushButton:hover { background-color: #ff7b86; }
        """)
        self.btn_render.clicked.connect(self._on_render_clicked)
        layout.addWidget(self.btn_render)

    def _on_browse_clicked(self):
        # Gunakan Service, jangan panggil QFileDialog langsung
        path = MediaDialogService.get_save_location(self, self.txt_path.text())
        if path:
            self.txt_path.setText(path)

    def _on_render_clicked(self):
        # Kumpulkan data form, kirim ke Logic
        data = {
            "output_path": self.txt_path.text(),
            "resolution": self.combo_res.currentText(),
            "fps": self.combo_fps.currentText()
        }
        self.sig_request_render.emit(data)