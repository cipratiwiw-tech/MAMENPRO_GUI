# gui/right_panel/sections/color_section.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSlider, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
from ..base_section import BaseSection

class ColorSection(BaseSection):
    def __init__(self, parent=None):
        super().__init__("COLOR & EFFECTS", parent)
        
        # --- TONE ---
        self.add_header("TONE")
        self.slider_bright = self._add_slider("Brightness", -100, 100, "color.brightness")
        self.slider_contrast = self._add_slider("Contrast", -100, 100, "color.contrast")
        self.slider_exposure = self._add_slider("Exposure", -100, 100, "color.exposure")
        
        # --- COLOR ---
        self.add_header("COLOR")
        self.slider_sat = self._add_slider("Saturation", -100, 100, "color.saturation")
        self.slider_hue = self._add_slider("Hue Shift", -180, 180, "color.hue")
        self.slider_temp = self._add_slider("Temp", -100, 100, "color.temperature")

        # --- FX ---
        self.add_header("FX")
        self.slider_blur = self._add_slider("Gaussian Blur", 0, 50, "effect.blur")
        self.slider_vignette = self._add_slider("Vignette", 0, 100, "effect.vignette")

        # Reset Button
        self.btn_reset = QPushButton("Reset Color")
        self.btn_reset.setStyleSheet("background: #3e4451; color: white; border: none; padding: 5px; margin-top: 10px;")
        self.btn_reset.clicked.connect(self._reset_all)
        self.form_layout.addRow(self.btn_reset)

    def add_header(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #56b6c2; font-weight: bold; margin-top: 5px; margin-bottom: 2px;")
        self.form_layout.addRow(lbl)

    def _add_slider(self, label, min_v, max_v, path):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_v, max_v)
        
        lbl_val = QLabel("0")
        lbl_val.setFixedWidth(30)
        lbl_val.setAlignment(Qt.AlignRight)
        
        slider.valueChanged.connect(lambda v: lbl_val.setText(str(v)))
        
        h = QHBoxLayout()
        h.addWidget(slider)
        h.addWidget(lbl_val)
        w = QWidget(); w.setLayout(h)
        
        # Register ke BaseSection
        self.add_row(label, w, path, control_widget=slider)
        return slider

    def _reset_all(self):
        # Reset visual slider ke 0 (default)
        # Sinyal akan otomatis terkirim karena BaseSection memantau valueChanged
        self.slider_bright.setValue(0)
        self.slider_contrast.setValue(0)
        self.slider_exposure.setValue(0)
        self.slider_sat.setValue(0)
        self.slider_hue.setValue(0)
        self.slider_temp.setValue(0)
        self.slider_blur.setValue(0)
        self.slider_vignette.setValue(0)

    def apply_state(self, props: dict):
        c = props.get("color", {})
        fx = props.get("effect", {})
        
        self._set_widget_value("color.brightness", c.get("brightness", 0))
        self._set_widget_value("color.contrast", c.get("contrast", 0))
        self._set_widget_value("color.exposure", c.get("exposure", 0))
        
        self._set_widget_value("color.saturation", c.get("saturation", 0))
        self._set_widget_value("color.hue", c.get("hue", 0))
        self._set_widget_value("color.temperature", c.get("temperature", 0))
        
        self._set_widget_value("effect.blur", fx.get("blur", 0))
        self._set_widget_value("effect.vignette", fx.get("vignette", 0))