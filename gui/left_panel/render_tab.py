from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Signal, Qt

class RenderTab(QWidget): # Kita tetap pakai nama file ini, tapi visualnya jadi Toolbar
    sig_start_render = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50) # Batasi tinggi agar tidak memakan tempat preview
        self.setStyleSheet("""
            QWidget { background-color: #21252b; border-bottom: 1px solid #181a1f; }
            QLabel { color: #abb2bf; font-weight: bold; margin-right: 5px; }
            QComboBox { 
                background-color: #282c34; color: #dcdcdc; border: 1px solid #3e4451; 
                padding: 4px; border-radius: 4px; min-width: 80px;
            }
            QPushButton {
                background-color: #98c379; color: #282c34; font-weight: bold;
                border-radius: 4px; padding: 6px 15px;
            }
            QPushButton:hover { background-color: #a5d482; }
            QPushButton:pressed { background-color: #8eb371; }
        """)
        self._init_ui()

    def _init_ui(self):
        # Gunakan Horizontal Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5) # Margin tipis
        layout.setSpacing(15)

        # LABEL JUDUL (Opsional, atau dihapus biar clean)
        lbl_title = QLabel("EXPORT:")
        lbl_title.setStyleSheet("color: #61afef;")
        layout.addWidget(lbl_title)

        # 1. RESOLUTION
        layout.addWidget(QLabel("Res:"))
        self.combo_res = QComboBox()
        self.combo_res.addItems(["1920x1080 (1080p)", "1280x720 (720p)", "1080x1920 (TikTok)", "1080x1080 (Square)"])
        layout.addWidget(self.combo_res)

        # 2. FPS
        layout.addWidget(QLabel("FPS:"))
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["30", "60", "24", "25"])
        self.combo_fps.setFixedWidth(60)
        layout.addWidget(self.combo_fps)

        # 3. QUALITY
        layout.addWidget(QLabel("Qual:"))
        self.combo_qual = QComboBox()
        self.combo_qual.addItems(["High", "Medium", "Low"])
        self.combo_qual.setFixedWidth(80)
        layout.addWidget(self.combo_qual)

        # SPACER (Mendorong tombol export ke kanan atau tengah)
        layout.addStretch()

        # 4. EXPORT BUTTON
        self.btn_render = QPushButton("🚀 EXPORT VIDEO")
        self.btn_render.setCursor(Qt.PointingHandCursor)
        self.btn_render.clicked.connect(self._on_render_click)
        layout.addWidget(self.btn_render)

    def _on_render_click(self):
        # Ambil data
        res_text = self.combo_res.currentText()
        width, height = self._parse_res(res_text)
        
        config = {
            "width": width,
            "height": height,
            "fps": int(self.combo_fps.currentText()),
            "quality": self.combo_qual.currentText().lower(),
            "format": "mp4"
        }
        self.sig_start_render.emit(config)

    def _parse_res(self, text):
        # Simple parser "1920x1080 ..." -> 1920, 1080
        try:
            parts = text.split(" ")[0].split("x")
            return int(parts[0]), int(parts[1])
        except:
            return 1920, 1080