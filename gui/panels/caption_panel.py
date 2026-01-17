# gui/panels/caption_panel.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QComboBox, QSpinBox, QFormLayout, QGroupBox)
from PySide6.QtCore import Signal

class CaptionPanel(QWidget):
    # SIGNAL OUT: (config_dict)
    # Panel tidak perlu kirim layer_id, biar Controller yang ambil dari Selection
    sig_request_caption = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        lbl = QLabel("AUTO CAPTION (AI)")
        lbl.setStyleSheet("font-weight: bold; color: #c678dd; margin-bottom: 10px;")
        layout.addWidget(lbl)

        # Config Group
        group = QGroupBox("Settings")
        group.setStyleSheet("QGroupBox { border: 1px solid #3e4451; margin-top: 10px; }")
        form = QFormLayout(group)

        # Language
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Indonesian", "English", "Javanese"])
        form.addRow("Language:", self.combo_lang)

        # Max Words per Line
        self.spin_words = QSpinBox()
        self.spin_words.setRange(1, 10)
        self.spin_words.setValue(5)
        form.addRow("Max Words:", self.spin_words)

        layout.addWidget(group)
        layout.addStretch()

        # Action Button
        self.btn_generate = QPushButton("🎙️ Generate Captions")
        self.btn_generate.setStyleSheet("""
            QPushButton { 
                background-color: #c678dd; color: white; 
                font-weight: bold; padding: 12px; border-radius: 4px; 
            }
            QPushButton:hover { background-color: #d19aed; }
        """)
        self.btn_generate.clicked.connect(self._on_generate_click)
        layout.addWidget(self.btn_generate)

    def _on_generate_click(self):
        # Bungkus config
        config = {
            "language": self.combo_lang.currentText().lower(),
            "max_words": self.spin_words.value()
        }
        self.sig_request_caption.emit(config)