# gui/right_panel/sections/timing_section.py
from PySide6.QtWidgets import QHBoxLayout, QWidget, QCheckBox
from ..base_section import BaseSection, SmartSpinBox

class TimingSection(BaseSection):
    def __init__(self, parent=None):
        print("[TIMING] Initializing Section...") # LOG
        super().__init__("TIMING", parent)
        
        # --- START TIME ---
        self.spin_start = self._create_spin(0, 3600, step=0.1, suffix=" s")
        self.add_row("Start Time:", self.spin_start, "timing.start_time")
        
        # --- DURATION ---
        self.spin_duration = self._create_spin(0.1, 3600, step=0.1, suffix=" s")
        self.add_row("Duration:", self.spin_duration, "timing.duration")
        
        # --- SPEED ---
        self.spin_speed = self._create_spin(0.1, 10.0, step=0.1, suffix="x")
        self.add_row("Speed:", self.spin_speed, "timing.speed")
        print("[TIMING] Section Ready") # LOG

    def _create_spin(self, min_val, max_val, step=1.0, suffix=""):
        sb = SmartSpinBox()
        sb.setRange(min_val, max_val)
        sb.setSingleStep(step)
        sb.setSuffix(suffix)
        sb.setStyleSheet("background-color: #2c313a; color: #dcdcdc; border: 1px solid #3e4451;")
        return sb

    def apply_state(self, props: dict):
        t = props.get("timing", {})
        print(f"[TIMING] apply_state: {t}") # LOG DATA MASUK
        
        self._set_widget_value("timing.start_time", t.get("start_time", 0.0))
        self._set_widget_value("timing.duration", t.get("duration", 5.0))
        self._set_widget_value("timing.speed", t.get("speed", 1.0))