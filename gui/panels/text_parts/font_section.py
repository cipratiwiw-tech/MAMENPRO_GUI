# gui/panels/text_parts/font_section.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFontComboBox, QSpinBox
from PySide6.QtCore import Signal

class FontSection(QWidget):
    sig_font_changed = Signal(dict) # {font_family, font_size}

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        # Font Family
        layout.addWidget(QLabel("Font Family:"))
        self.combo_font = QFontComboBox()
        self.combo_font.currentFontChanged.connect(self._emit_change)
        layout.addWidget(self.combo_font)

        # Font Size
        layout.addWidget(QLabel("Size:"))
        self.spin_size = QSpinBox()
        self.spin_size.setRange(10, 300)
        self.spin_size.setValue(60)
        self.spin_size.valueChanged.connect(self._emit_change)
        layout.addWidget(self.spin_size)

    def _emit_change(self):
        self.sig_font_changed.emit({
            "font_family": self.combo_font.currentFont().family(),
            "font_size": self.spin_size.value()
        })

    def set_values(self, props):
        if "font_family" in props: 
            self.combo_font.setCurrentFont(props["font_family"])
        if "font_size" in props: 
            self.spin_size.setValue(int(props["font_size"]))