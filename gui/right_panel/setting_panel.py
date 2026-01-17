# gui/right_panel/setting_panel.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                             QGridLayout, QLabel, QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import Signal, Qt

class SettingPanel(QWidget):
    # Sinyal saat user mengedit nilai (UI -> Logic)
    sig_property_changed = Signal(dict) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._block_signals = False # Flag untuk mencegah feedback loop visual
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # --- Transform Group ---
        group = QGroupBox("TRANSFORM")
        group.setStyleSheet("QGroupBox { font-weight: bold; color: #61afef; border: 1px solid #3e4451; margin-top: 20px; }")
        grid = QGridLayout(group)

        # X Position
        self.spin_x = self._create_spinbox(-3000, 3000, " px")
        grid.addWidget(QLabel("X:"), 0, 0)
        grid.addWidget(self.spin_x, 0, 1)

        # Y Position
        self.spin_y = self._create_spinbox(-3000, 3000, " px")
        grid.addWidget(QLabel("Y:"), 1, 0)
        grid.addWidget(self.spin_y, 1, 1)

        # Scale
        self.spin_scale = self._create_spinbox(1, 1000, " %")
        grid.addWidget(QLabel("Scale:"), 2, 0)
        grid.addWidget(self.spin_scale, 2, 1)
        
        # Rotation
        self.spin_rot = self._create_spinbox(-360, 360, " °")
        grid.addWidget(QLabel("Rotation:"), 3, 0)
        grid.addWidget(self.spin_rot, 3, 1)

        layout.addWidget(group)
        layout.addStretch()

        # Connect internal signals
        self.spin_x.valueChanged.connect(self._on_value_changed)
        self.spin_y.valueChanged.connect(self._on_value_changed)
        self.spin_scale.valueChanged.connect(self._on_value_changed)
        self.spin_rot.valueChanged.connect(self._on_value_changed)

    def _create_spinbox(self, min_val, max_val, suffix):
        sb = QSpinBox()
        sb.setRange(min_val, max_val)
        sb.setSuffix(suffix)
        sb.setStyleSheet("background-color: #2c313a; border: 1px solid #3e4451; padding: 4px;")
        return sb

    def _on_value_changed(self):
        if self._block_signals: return

        # Bungkus data dalam dict
        data = {
            "x": self.spin_x.value(),
            "y": self.spin_y.value(),
            "scale": self.spin_scale.value(),
            "rotation": self.spin_rot.value()
        }
        self.sig_property_changed.emit(data)

    # --- PERINTAH DARI BINDER (LOGIC -> UI) ---
    def update_form_visual(self, props: dict):
        """Update tampilan form tanpa memicu sinyal balik"""
        self._block_signals = True # Cegah loop: Controller -> UI -> Controller
        
        if "x" in props: self.spin_x.setValue(int(props["x"]))
        if "y" in props: self.spin_y.setValue(int(props["y"]))
        if "scale" in props: self.spin_scale.setValue(int(props["scale"]))
        if "rotation" in props: self.spin_rot.setValue(int(props["rotation"]))
        
        self._block_signals = False
        
    def clear_form(self):
        self._block_signals = True
        self.spin_x.setValue(0)
        self.spin_y.setValue(0)
        self.spin_scale.setValue(100)
        self.spin_rot.setValue(0)
        self._block_signals = False