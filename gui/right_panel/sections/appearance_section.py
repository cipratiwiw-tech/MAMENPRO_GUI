# gui/right_panel/sections/appearance_section.py
from PySide6.QtWidgets import QSlider, QLabel, QHBoxLayout, QWidget, QComboBox
from PySide6.QtCore import Qt
from ..base_section import BaseSection

class AppearanceSection(BaseSection):
    def __init__(self, parent=None):
        super().__init__("APPEARANCE", parent)
        
        # --- OPACITY ---
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(0, 100)
        
        self.lbl_opacity = QLabel("100%")
        self.lbl_opacity.setFixedWidth(40)
        self.lbl_opacity.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Container menyimpan Slider + Label
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0,0,0,0)
        h_layout.addWidget(self.slider_opacity)
        h_layout.addWidget(self.lbl_opacity)
        container = QWidget(); container.setLayout(h_layout)
        
        # UI Feedback
        self.slider_opacity.valueChanged.connect(self._on_opacity_ui_change)
       
        # Register: Tampilkan 'container', tapi logika ikut 'slider_opacity'
        self.add_row(
            "Opacity:", 
            container,            # Layout Widget
            "appearance.opacity",
            control_widget=self.slider_opacity, # Logic Widget
            converter_in=lambda x: int(float(x) * 100), 
            converter_out=lambda x: float(x) / 100.0     
        )
        
        # --- BLEND MODE ---
        self.combo_blend = QComboBox()
        self.combo_blend.addItems(["Normal", "Multiply", "Screen", "Overlay", "Darken", "Lighten"])
        self.combo_blend.setStyleSheet("background-color: #2c313a; color: #dcdcdc; border: 1px solid #3e4451;")
        
        self.add_row("Blend Mode:", self.combo_blend, "appearance.blend_mode")

    def apply_state(self, props: dict):
        a = props["appearance"]
        self._set_widget_value("appearance.opacity", a["opacity"])
        self._set_widget_value("appearance.blend_mode", a["blend_mode"])
        
    
    def _on_opacity_ui_change(self, v):
        self.lbl_opacity.setText(f"{v}%")