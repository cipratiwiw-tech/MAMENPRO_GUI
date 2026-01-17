# gui/left_panel/render_tab.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QLineEdit, QComboBox, QFormLayout, QHBoxLayout)
from PySide6.QtCore import Signal
from gui.services.media_dialog_service import MediaDialogService
import os # <--- [TAMBAHAN IMPORT]

class RenderTab(QWidget):
    # SIGNAL OUT: User request render dengan config ini
    sig_request_render = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl = QLabel("EXPORT VIDEO")
        lbl.setStyleSheet("font-weight: bold; color: #e06c75; margin-bottom: 10px;")
        layout.addWidget(lbl)

        # FORM
        form = QFormLayout()
        
        # Output Path
        self.txt_path = QLineEdit("output.mp4")
        self.btn_browse = QPushButton("...")
        self.btn_browse.setFixedWidth(40)
        self.btn_browse.clicked.connect(self._on_browse)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.txt_path)
        path_layout.addWidget(self.btn_browse)
        form.addRow("File:", path_layout)

        # Resolution
        self.combo_res = QComboBox()
        self.combo_res.addItems(["1920x1080 (FHD)", "1280x720 (HD)", "1080x1920 (TikTok)"])
        form.addRow("Res:", self.combo_res)

        # FPS
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["30 FPS", "60 FPS", "24 FPS"])
        form.addRow("FPS:", self.combo_fps)

        layout.addLayout(form)
        layout.addStretch()

        # ACTION BUTTON
        self.btn_render = QPushButton("🚀 START RENDER")
        self.btn_render.setStyleSheet("""
            QPushButton { background-color: #e06c75; color: white; font-weight: bold; padding: 12px; border-radius: 4px; }
            QPushButton:hover { background-color: #ff7b86; }
        """)
        self.btn_render.clicked.connect(self._on_render_click)
        layout.addWidget(self.btn_render)

    def _on_browse(self):
        path = MediaDialogService.get_save_location(self, self.txt_path.text())
        if path:
            self.txt_path.setText(path)

    def _on_render_click(self):
        # 1. Parsing Resolution
        res_text = self.combo_res.currentText() 
        res_part = res_text.split(" ")[0]       
        w_str, h_str = res_part.split("x")
        width = int(w_str)
        height = int(h_str)

        # 2. Parsing FPS
        fps_text = self.combo_fps.currentText()
        fps = int(fps_text.split(" ")[0])       

        # 3. [PERBAIKAN VITAL] Validasi Ekstensi Path
        raw_path = self.txt_path.text().strip()
        if not raw_path:
            raw_path = "output.mp4" # Default jika kosong
            
        # Cek apakah user lupa nulis .mp4
        filename, ext = os.path.splitext(raw_path)
        if not ext:
            raw_path += ".mp4" # Paksa tambah .mp4
        
        # Update UI text agar user sadar
        self.txt_path.setText(raw_path)

        # 4. Bungkus Config
        config = {
            "path": raw_path, 
            "width": width,
            "height": height,
            "fps": fps
        }
        
        self.sig_request_render.emit(config)