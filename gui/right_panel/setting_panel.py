# gui/right_panel/setting_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PySide6.QtCore import Signal, Qt

# Import Sections
from .sections.transform_section import TransformSection
from .sections.appearance_section import AppearanceSection
from .sections.timing_section import TimingSection
from .sections.audio_section import AudioSection

class StateAdapter:
    @staticmethod
    def to_ui_structure(flat_props: dict) -> dict:
        return {
            "transform": {
                "position": { "x": flat_props.get("x", 0), "y": flat_props.get("y", 0) },
                "scale": { 
                    "x": flat_props.get("scale_x", flat_props.get("scale", 100)),
                    "y": flat_props.get("scale_y", flat_props.get("scale", 100))
                },
                "rotation": flat_props.get("rotation", 0),
                "anchor": { "x": flat_props.get("anchor_x", 0.5), "y": flat_props.get("anchor_y", 0.5) }
            },
            "appearance": {
                "opacity": flat_props.get("opacity", 1.0),
                "blend_mode": flat_props.get("blend_mode", "Normal")
            },
            "timing": {
                "start_time": flat_props.get("start_time", 0.0),
                "duration": flat_props.get("duration", 5.0),
                "speed": flat_props.get("speed", 1.0)
            },
            "audio": {
                "volume": flat_props.get("volume", 1.0),
                "mute": flat_props.get("mute", False)
            }
        }

    @staticmethod
    def to_legacy_update(path: str, value) -> dict:
        map_table = {
            "transform.position.x": "x", "transform.position.y": "y",
            "transform.scale.x": "scale_x", "transform.scale.y": "scale_y",
            "transform.rotation": "rotation",
            "transform.anchor.x": "anchor_x", "transform.anchor.y": "anchor_y",
            "appearance.opacity": "opacity", "appearance.blend_mode": "blend_mode",
            "timing.start_time": "start_time", "timing.duration": "duration", "timing.speed": "speed",
            "audio.volume": "volume", "audio.mute": "mute"
        }
        if path in map_table:
            return {map_table[path]: value}
        return {}

class SettingPanel(QWidget):
    sig_property_changed = Signal(str, object) 
    sig_property_update = Signal(dict)

    def __init__(self, parent=None):
        print("[PANEL] Initializing SettingPanel...") # LOG
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()
        self._init_sections()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignTop)
        
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)
        
        self.lbl_empty = QLabel("Select a layer")
        self.lbl_empty.setAlignment(Qt.AlignCenter)
        self.lbl_empty.setStyleSheet("color: #5c6370; margin-top: 50px;")
        self.container_layout.addWidget(self.lbl_empty)

    def _init_sections(self):
        self.sections = []
        
        # Instantiate All Sections
        self.sec_transform = TransformSection()
        self.sec_appearance = AppearanceSection()
        self.sec_timing = TimingSection()
        self.sec_audio = AudioSection()
        
        # Register
        self._register_section(self.sec_transform)
        self._register_section(self.sec_appearance)
        self._register_section(self.sec_timing)
        self._register_section(self.sec_audio)

    def _register_section(self, section):
        self.container_layout.addWidget(section)
        self.sections.append(section)
        section.hide()
        section.sig_edit_changed.connect(self._on_section_change)

    def _on_section_change(self, path, value):
        print(f"[PANEL] Signal Emit: {path} = {value}") # LOG SIGNAL KELUAR
        self.sig_property_changed.emit(path, value)
        legacy_payload = StateAdapter.to_legacy_update(path, value)
        if legacy_payload:
            self.sig_property_update.emit(legacy_payload)

    def set_values(self, layer_data):
        if not layer_data:
            print("[PANEL] No layer selected (Clearing UI)")
            self._show_empty(True)
            return

        self._show_empty(False)
        
        flat_props = layer_data.properties
        clean_props = StateAdapter.to_ui_structure(flat_props)
        l_type = layer_data.type
        
        print(f"[PANEL] set_values -> Layer Type: {l_type}") # LOG TIPE LAYER
        
        # --- VISIBILITY RULES ---
        # 1. Transform: Visual Items
        vis_transform = l_type in ['video', 'image', 'text', 'shape', 'caption']
        self.sec_transform.setVisible(vis_transform)
        
        # 2. Appearance: Visual Items
        vis_appear = l_type in ['video', 'image', 'text', 'shape']
        self.sec_appearance.setVisible(vis_appear)
        
        # 3. Timing: All Time-based Items
        vis_timing = l_type in ['video', 'image', 'text', 'audio', 'shape', 'caption']
        self.sec_timing.setVisible(vis_timing)
        
        # 4. Audio: Only Items with Sound
        vis_audio = l_type in ['video', 'audio']
        self.sec_audio.setVisible(vis_audio)
        
        print(f"[PANEL] Visibility -> Trans:{vis_transform}, App:{vis_appear}, Time:{vis_timing}, Audio:{vis_audio}")

        # Populate UI
        for section in self.sections:
            if section.isVisible():
                section.apply_state(clean_props)

    def _show_empty(self, show):
        self.lbl_empty.setVisible(show)
        for section in self.sections:
            section.setVisible(False)