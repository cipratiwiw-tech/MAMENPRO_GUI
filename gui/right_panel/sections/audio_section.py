# gui/right_panel/sections/audio_section.py
from PySide6.QtWidgets import QSlider, QLabel, QHBoxLayout, QWidget, QCheckBox
from PySide6.QtCore import Qt
from ..base_section import BaseSection

class AudioSection(BaseSection):
    def __init__(self, parent=None):
        print("[AUDIO] Initializing Section...") # LOG
        super().__init__("AUDIO", parent)
        
        # --- VOLUME ---
        self.slider_vol = QSlider(Qt.Horizontal)
        self.slider_vol.setRange(0, 200)
        
        self.lbl_vol = QLabel("100%")
        self.lbl_vol.setFixedWidth(40)
        self.lbl_vol.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0,0,0,0)
        h_layout.addWidget(self.slider_vol)
        h_layout.addWidget(self.lbl_vol)
        container = QWidget(); container.setLayout(h_layout)
        
        self.slider_vol.valueChanged.connect(lambda v: self.lbl_vol.setText(f"{v}%"))
        
        # PENTING: Menggunakan control_widget agar container tidak dihapus
        self.add_row(
            "Volume:", 
            container, 
            "audio.volume",
            control_widget=self.slider_vol,
            converter_in=lambda x: int(float(x) * 100),
            converter_out=lambda x: float(x) / 100.0
        )
        
        # --- MUTE ---
        self.chk_mute = QCheckBox("Mute Audio")
        self.chk_mute.setStyleSheet("color: #dcdcdc;")
        self.add_row("", self.chk_mute, "audio.mute")
        
        self.chk_mute.stateChanged.connect(lambda v: self._on_mute_change(v))
        print("[AUDIO] Section Ready") # LOG

    def _on_mute_change(self, val_int):
        is_muted = val_int == 2
        print(f"[AUDIO] User changed Mute -> {is_muted}") # LOG INTERAKSI
        self.sig_edit_changed.emit("audio.mute", is_muted)

    def apply_state(self, props: dict):
        a = props.get("audio", {})
        print(f"[AUDIO] apply_state: {a}") # LOG DATA MASUK
        
        self._set_widget_value("audio.volume", a.get("volume", 1.0))
        
        is_muted = a.get("mute", False)
        self.chk_mute.blockSignals(True)
        self.chk_mute.setChecked(is_muted)
        self.chk_mute.blockSignals(False)