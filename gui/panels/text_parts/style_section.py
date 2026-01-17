# gui/panels/text_parts/style_section.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QColorDialog
from PySide6.QtCore import Signal

class StyleSection(QWidget):
    sig_style_changed = Signal(dict) # {color, is_bold}

    def __init__(self):
        super().__init__()
        self.current_color = "#ffffff"
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        # Color Picker Button
        layout.addWidget(QLabel("Color:"))
        self.btn_color = QPushButton(self.current_color)
        self.btn_color.setStyleSheet(f"background-color: {self.current_color}; color: black; border: 1px solid #555;")
        self.btn_color.clicked.connect(self._pick_color)
        layout.addWidget(self.btn_color)
        
        # Bold Toggle (Contoh)
        self.btn_bold = QPushButton("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setStyleSheet("font-weight: bold;")
        self.btn_bold.toggled.connect(self._emit_change)
        layout.addWidget(self.btn_bold)

    def _pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()
            self.btn_color.setText(self.current_color)
            self.btn_color.setStyleSheet(f"background-color: {self.current_color}; color: black;")
            self._emit_change()

    def _emit_change(self):
        self.sig_style_changed.emit({
            "text_color": self.current_color,
            "is_bold": self.btn_bold.isChecked()
        })
        
    def set_values(self, props):
        if "text_color" in props:
            self.current_color = props["text_color"]
            self.btn_color.setText(self.current_color)
            self.btn_color.setStyleSheet(f"background-color: {self.current_color};")