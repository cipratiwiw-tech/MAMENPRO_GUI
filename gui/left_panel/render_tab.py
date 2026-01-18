from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, 
    QPushButton, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Signal, Qt

class RenderTab(QWidget):
    # Signals
    sig_start_render = Signal(dict)
    sig_stop_render = Signal()
    sig_select_output_dir = Signal() # Request untuk memilih folder
    sig_open_output_dir = Signal()   # Request untuk membuka folder

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setStyleSheet("""
            QWidget { background-color: #21252b; border-bottom: 1px solid #181a1f; }
            QLineEdit {
                background-color: #282c34; color: #9da5b4; 
                border: 1px solid #3e4451; border-radius: 4px; padding: 4px 8px;
            }
            QComboBox { 
                background-color: #282c34; color: #dcdcdc; 
                border: 1px solid #3e4451; padding: 4px; border-radius: 4px;
            }
            QPushButton {
                background-color: #3e4451; color: #dcdcdc; font-weight: bold;
                border-radius: 4px; padding: 6px 12px; border: none;
            }
            QPushButton:hover { background-color: #4b5263; }
            QPushButton#btn_export { background-color: #98c379; color: #282c34; }
            QPushButton#btn_export:hover { background-color: #a5d482; }
            QPushButton#btn_stop { background-color: #e06c75; color: white; }
            QPushButton#btn_stop:hover { background-color: #ef7c86; }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # 1. KOLOM PATH (Read Only)
        self.line_path = QLineEdit()
        self.line_path.setReadOnly(True)
        self.line_path.setPlaceholderText("Select Output Folder...")
        self.line_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.line_path)

        # 2. TOMBOL PILIH FOLDER
        self.btn_select = QPushButton("📂")
        self.btn_select.setToolTip("Pilih Folder Output")
        self.btn_select.setFixedWidth(35)
        self.btn_select.clicked.connect(self.sig_select_output_dir.emit)
        layout.addWidget(self.btn_select)

        # 3. TOMBOL BUKA FOLDER
        self.btn_open = QPushButton("↗️")
        self.btn_open.setToolTip("Buka Folder di Explorer")
        self.btn_open.setFixedWidth(35)
        self.btn_open.clicked.connect(self.sig_open_output_dir.emit)
        layout.addWidget(self.btn_open)

        # 4. KUALITAS RENDER
        self.combo_qual = QComboBox()
        self.combo_qual.addItems(["High", "Medium", "Low"])
        self.combo_qual.setToolTip("Kualitas Render")
        layout.addWidget(self.combo_qual)

        # 5. TOMBOL EXPORT
        self.btn_render = QPushButton("🚀 EXPORT")
        self.btn_render.setObjectName("btn_export")
        self.btn_render.setCursor(Qt.PointingHandCursor)
        self.btn_render.clicked.connect(self._on_render_click)
        layout.addWidget(self.btn_render)

        # 6. TOMBOL STOP (Hidden by default)
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setVisible(False)
        self.btn_stop.clicked.connect(self.sig_stop_render.emit)
        layout.addWidget(self.btn_stop)

    def set_output_path(self, path):
        """Update teks di kolom path"""
        self.line_path.setText(path)
        self.line_path.setToolTip(path)

    def set_rendering_state(self, is_rendering):
        """Toggle tombol Export vs Stop"""
        self.btn_render.setVisible(not is_rendering)
        self.btn_stop.setVisible(is_rendering)
        self.combo_qual.setEnabled(not is_rendering)
        self.btn_select.setEnabled(not is_rendering)

    def _on_render_click(self):
        # Kirim config render
        config = {
            "quality": self.combo_qual.currentText().lower(),
            "path": self.line_path.text()
        }
        self.sig_start_render.emit(config)