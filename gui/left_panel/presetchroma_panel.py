# gui/left_panel/presetchroma_panel.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QGridLayout, QSlider, QHBoxLayout)
from PySide6.QtCore import Signal, Qt

class PresetChromaPanel(QWidget):
    # SIGNAL OUT: (color_hex, threshold)
    sig_apply_chroma = Signal(str, float)
    sig_remove_chroma = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl = QLabel("CHROMA KEY PRESETS")
        lbl.setStyleSheet("font-weight: bold; color: #98c379;")
        layout.addWidget(lbl)
        
        # Grid Tombol Warna
        grid = QGridLayout()
        
        self.btn_green = self._create_color_btn("Green Screen", "#00ff00")
        self.btn_blue = self._create_color_btn("Blue Screen", "#0000ff")
        self.btn_black = self._create_color_btn("Black BG", "#000000")
        self.btn_white = self._create_color_btn("White BG", "#ffffff")

        grid.addWidget(self.btn_green, 0, 0)
        grid.addWidget(self.btn_blue, 0, 1)
        grid.addWidget(self.btn_black, 1, 0)
        grid.addWidget(self.btn_white, 1, 1)
        layout.addLayout(grid)

        # Threshold Slider (Kekuatan Chroma)
        layout.addWidget(QLabel("Intensity:"))
        self.slider_threshold = QSlider(Qt.Horizontal)
        self.slider_threshold.setRange(1, 100)
        self.slider_threshold.setValue(15) # Default 0.15 equivalent
        layout.addWidget(self.slider_threshold)

        # Remove Button
        self.btn_remove = QPushButton("🚫 Remove Chroma")
        self.btn_remove.setStyleSheet("background-color: #e06c75; color: white; border-radius: 4px; padding: 5px;")
        self.btn_remove.clicked.connect(self.sig_remove_chroma.emit)
        layout.addWidget(self.btn_remove)
        
        layout.addStretch()

    def _create_color_btn(self, text, color_hex):
        btn = QPushButton(text)
        # Menampilkan indikator warna di border
        btn.setStyleSheet(f"""
            QPushButton {{ border-left: 5px solid {color_hex}; padding: 10px; text-align: left; background-color: #2c313a; }}
            QPushButton:hover {{ background-color: #3e4451; }}
        """)
        btn.clicked.connect(lambda: self._on_preset_clicked(color_hex))
        return btn

    def _on_preset_clicked(self, color_hex):
        threshold = self.slider_threshold.value() / 100.0
        self.sig_apply_chroma.emit(color_hex, threshold)