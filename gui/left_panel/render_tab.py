# gui/left_panel/render_tab.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFileDialog, QHBoxLayout
)
from PySide6.QtCore import Signal


class RenderTab(QWidget):
    sig_start_render = Signal(dict)

    def __init__(self):
        super().__init__()

        # 🔧 Layout utama — dipadatkan
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(6)
        self.layout.setContentsMargins(8, 8, 8, 8)

        # ===============================
        # Title
        # ===============================
        lbl_title = QLabel("Export Settings")
        lbl_title.setStyleSheet("""
            font-weight: bold;
            font-size: 13px;
            color: #ccc;
            padding-bottom: 4px;
        """)
        self.layout.addWidget(lbl_title)

        # ===============================
        # Output Path
        # ===============================
        lbl_output = QLabel("Output File")
        lbl_output.setStyleSheet("color: #aaa;")
        self.layout.addWidget(lbl_output)

        path_layout = QHBoxLayout()
        path_layout.setSpacing(4)

        self.input_path = QLineEdit("output.mp4")
        self.input_path.setFixedHeight(26)
        self.input_path.setStyleSheet("""
            padding: 4px;
            color: #fff;
            background: #333;
            border: 1px solid #555;
        """)
        path_layout.addWidget(self.input_path)

        btn_browse = QPushButton("...")
        btn_browse.setFixedSize(28, 26)
        btn_browse.setStyleSheet("background: #444; color: white;")
        btn_browse.clicked.connect(self._browse_file)
        path_layout.addWidget(btn_browse)

        self.layout.addLayout(path_layout)

        # ===============================
        # FPS
        # ===============================
        self.layout.addWidget(QLabel("Frame Rate"))

        self.combo_fps = QComboBox()
        self.combo_fps.setFixedHeight(26)
        self.combo_fps.addItems(["24", "30", "60"])
        self.combo_fps.setCurrentText("30")
        self.layout.addWidget(self.combo_fps)

        # ===============================
        # Quality
        # ===============================
        self.layout.addWidget(QLabel("Quality"))

        self.combo_quality = QComboBox()
        self.combo_quality.setFixedHeight(26)
        self.combo_quality.addItems([
            "High (CRF 18)",
            "Medium (CRF 23)",
            "Low (CRF 28)"
        ])
        self.layout.addWidget(self.combo_quality)

        # Dorong tombol ke bawah
        self.layout.addStretch()

        # ===============================
        # Render Button
        # ===============================
        self.btn_render = QPushButton("START RENDER")
        self.btn_render.setFixedHeight(36)
        self.btn_render.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #0098ff; }
            QPushButton:pressed { background-color: #005a9e; }
        """)
        self.btn_render.clicked.connect(self._on_render_click)
        self.layout.addWidget(self.btn_render)

    # ===============================
    # Slots
    # ===============================
    def _browse_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Video", "output.mp4", "Video Files (*.mp4)"
        )
        if path:
            self.input_path.setText(path)

    def _on_render_click(self):
        settings = {
            "output_path": self.input_path.text() or "output.mp4",
            "fps": int(self.combo_fps.currentText()),
            "quality": self.combo_quality.currentText()
        }
        self.sig_start_render.emit(settings)
