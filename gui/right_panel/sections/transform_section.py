# gui/right_panel/sections/transform_section.py
from PySide6.QtWidgets import QHBoxLayout, QWidget
from ..base_section import BaseSection, SmartSpinBox

class TransformSection(BaseSection):
    def __init__(self, parent=None):
        super().__init__("TRANSFORM", parent)
        
        # --- POSITION (Pixel) ---
        self.spin_pos_x = self._create_spin(-99999, 99999, suffix=" px")
        self.spin_pos_y = self._create_spin(-99999, 99999, suffix=" px")
        self.add_row("Position X:", self.spin_pos_x, "transform.position.x")
        self.add_row("Position Y:", self.spin_pos_y, "transform.position.y")
        
        # --- SCALE (Percentage) ---
        # Logic: 100% (UI) = 100.0 (Model)
        self.spin_scale_x = self._create_spin(0, 10000, suffix=" %")
        self.spin_scale_y = self._create_spin(0, 10000, suffix=" %")
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.spin_scale_x)
        h_layout.addWidget(self.spin_scale_y)
        container = QWidget(); container.setLayout(h_layout)
        
        # Manual Add Row untuk layout horizontal, tapi register path manual
        self.form_layout.addRow("Scale (X, Y):", container)
        
        # Register widget ke BaseSection logic secara manual
        self._prop_map["transform.scale.x"] = {"widget": self.spin_scale_x, "in": lambda x: x, "out": lambda x: x}
        self._prop_map["transform.scale.y"] = {"widget": self.spin_scale_y, "in": lambda x: x, "out": lambda x: x}
        self._connect_lifecycle(self.spin_scale_x, "transform.scale.x")
        self._connect_lifecycle(self.spin_scale_y, "transform.scale.y")
        
        # --- ROTATION (Degree) ---
        self.spin_rot = self._create_spin(-3600, 3600, suffix=" °")
        self.add_row("Rotation:", self.spin_rot, "transform.rotation")
        
        # --- ANCHOR (Normalized 0.0 - 1.0) ---
        # Range: -2.0 to 2.0 (Allow pivoting outside frame slightly)
        # Standard Center: 0.5, 0.5
        self.spin_anchor_x = self._create_spin(-2.0, 2.0, step=0.1)
        self.spin_anchor_y = self._create_spin(-2.0, 2.0, step=0.1)
        self.add_row("Anchor X:", self.spin_anchor_x, "transform.anchor.x")
        self.add_row("Anchor Y:", self.spin_anchor_y, "transform.anchor.y")

    def _create_spin(self, min_val, max_val, step=1.0, suffix=""):
        sb = SmartSpinBox()
        sb.setRange(min_val, max_val)
        sb.setSingleStep(step)
        sb.setSuffix(suffix)
        sb.setKeyboardTracking(False)
        sb.setStyleSheet("background-color: #2c313a; color: #dcdcdc; border: 1px solid #3e4451;")
        return sb

    def apply_state(self, props: dict):
        """
        PURE VIEW LOGIC.
        Expects: { "transform": { "position": { "x": ... }, ... } }
        No defaults, no fallbacks. If structure missing -> Crash/Error (Good, for strictness).
        """
        t = props["transform"]
        
        self._set_widget_value("transform.position.x", t["position"]["x"])
        self._set_widget_value("transform.position.y", t["position"]["y"])
        
        self._set_widget_value("transform.scale.x", t["scale"]["x"])
        self._set_widget_value("transform.scale.y", t["scale"]["y"])
        
        self._set_widget_value("transform.rotation", t["rotation"])
        
        self._set_widget_value("transform.anchor.x", t["anchor"]["x"])
        self._set_widget_value("transform.anchor.y", t["anchor"]["y"])