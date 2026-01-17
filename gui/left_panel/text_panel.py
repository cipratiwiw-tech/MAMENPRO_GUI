# gui/left_panel/text_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal

class TextPanel(QWidget):
    # Signal: text_content, font_size
    sig_add_text = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl = QLabel("TEXT PRESETS")
        lbl.setStyleSheet("font-weight: bold; color: #61afef; margin-bottom: 10px;")
        layout.addWidget(lbl)

        # Preset Buttons
        btn_heading = self._create_btn("Add Heading", "HEADING", 100)
        btn_sub = self._create_btn("Add Subheading", "Subheading", 60)
        btn_body = self._create_btn("Add Body Text", "Lorem ipsum dolor sit amet", 40)

        layout.addWidget(btn_heading)
        layout.addWidget(btn_sub)
        layout.addWidget(btn_body)
        
        layout.addStretch()

    def _create_btn(self, label, content, size):
        btn = QPushButton(label)
        btn.setStyleSheet("""
            QPushButton { 
                background-color: #2c313a; border: 1px solid #3e4451; 
                padding: 12px; text-align: left; margin-bottom: 5px;
            }
            QPushButton:hover { border-color: #61afef; background-color: #3e4451; }
        """)
        # Lambda default argument trick to bind values
        btn.clicked.connect(lambda checked=False, c=content, s=size: self.sig_add_text.emit(c, s))
        return btn
