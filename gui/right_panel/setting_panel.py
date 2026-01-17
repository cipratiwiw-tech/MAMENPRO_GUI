# gui/right_panel/setting_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PySide6.QtCore import Signal, Qt

# Import Sections
from .sections.transform_section import TransformSection
from .sections.appearance_section import AppearanceSection
from .sections.timing_section import TimingSection
from .sections.audio_section import AudioSection
from .sections.text_section import TextSection

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
            },
            "text": {
                "content": flat_props.get("text_content", ""),
                "font_family": flat_props.get("font_family", "Arial"),
                "font_size": flat_props.get("font_size", 60),
                "color": flat_props.get("text_color", "#ffffff"),
                "weight": flat_props.get("text_weight", "Normal"),
                "italic": flat_props.get("text_italic", False),
                "wrap": flat_props.get("text_wrap", False),
                
                "align": flat_props.get("text_align", "left"),
                "line_height": flat_props.get("line_height", 1.2),
                "letter_spacing": flat_props.get("letter_spacing", 0),
                
                "stroke_enabled": flat_props.get("stroke_enabled", False),
                "stroke_color": flat_props.get("stroke_color", "#000000"),
                "stroke_width": flat_props.get("stroke_width", 2),
                
                "shadow_enabled": flat_props.get("shadow_enabled", False),
                "shadow_color": flat_props.get("shadow_color", "#000000"),
                "shadow_blur": flat_props.get("shadow_blur", 5),
                "shadow_x": flat_props.get("shadow_x", 5),
                "shadow_y": flat_props.get("shadow_y", 5),
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
            "audio.volume": "volume", "audio.mute": "mute",
            
            # TEXT
            "text.content": "text_content",
            "text.font_family": "font_family",
            "text.font_size": "font_size",
            "text.color": "text_color",
            "text.weight": "text_weight",
            "text.italic": "text_italic",
            "text.wrap": "text_wrap",
            
            "text.align": "text_align",
            "text.line_height": "line_height",
            "text.letter_spacing": "letter_spacing",
            
            "text.stroke_enabled": "stroke_enabled",
            "text.stroke_color": "stroke_color",
            "text.stroke_width": "stroke_width",
            
            "text.shadow_enabled": "shadow_enabled",
            "text.shadow_color": "shadow_color",
            "text.shadow_blur": "shadow_blur",
            "text.shadow_x": "shadow_x",
            "text.shadow_y": "shadow_y",
        }
        if path in map_table:
            return {map_table[path]: value}
        return {}

class SettingPanel(QWidget):
    sig_property_changed = Signal(str, object) 
    sig_property_update = Signal(dict)

    def __init__(self, parent=None):
        print("[PANEL] Initializing SettingPanel...")
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
        
        self.sec_transform = TransformSection()
        self.sec_text = TextSection() # TEXT
        self.sec_appearance = AppearanceSection()
        self.sec_timing = TimingSection()
        self.sec_audio = AudioSection()
        
        self._register_section(self.sec_transform)
        self._register_section(self.sec_text)
        self._register_section(self.sec_appearance)
        self._register_section(self.sec_timing)
        self._register_section(self.sec_audio)

    def _register_section(self, section):
        self.container_layout.addWidget(section)
        self.sections.append(section)
        section.hide()
        section.sig_edit_changed.connect(self._on_section_change)

    def _on_section_change(self, path, value):
        print(f"[PANEL] Signal Emit: {path} = {value}")
        self.sig_property_changed.emit(path, value)
        legacy_payload = StateAdapter.to_legacy_update(path, value)
        if legacy_payload:
            self.sig_property_update.emit(legacy_payload)

    def set_values(self, layer_data):
        if not layer_data:
            self._show_empty(True)
            return

        self._show_empty(False)
        
        flat_props = layer_data.properties
        clean_props = StateAdapter.to_ui_structure(flat_props)
        l_type = layer_data.type
        
        # ==================================================
        # 🔥 SMART REORDERING & VISIBILITY 🔥
        # ==================================================
        
        if l_type in ['text', 'caption']:
            # Jika Text: Text Section Paling Atas
            # Transform Section TIDAK DIMASUKKAN ke list prioritas (akan di-hide di bawah)
            priority_order = [
                self.sec_text,
                self.sec_appearance,
                self.sec_timing,
                self.sec_audio
            ]
        else:
            # Jika Video/Image: Transform Section Paling Atas
            priority_order = [
                self.sec_transform,
                self.sec_text,
                self.sec_appearance,
                self.sec_timing,
                self.sec_audio
            ]
            
        # Reorder Layout
        for section in priority_order:
            self.container_layout.addWidget(section)

        # ==================================================
        # VISIBILITY RULES
        # ==================================================
        
        # [UPDATE] Transform hanya muncul untuk Video, Image, Shape. 
        # Text tidak perlu transform karena sudah ada di canvas (mouse)
        vis_transform = l_type in ['video', 'image', 'shape']
        self.sec_transform.setVisible(vis_transform)
        
        vis_appear = l_type in ['video', 'image', 'text', 'shape']
        self.sec_appearance.setVisible(vis_appear)
        
        vis_timing = l_type in ['video', 'image', 'text', 'audio', 'shape', 'caption']
        self.sec_timing.setVisible(vis_timing)
        
        vis_audio = l_type in ['video', 'audio']
        self.sec_audio.setVisible(vis_audio)

        vis_text = l_type in ['text', 'caption']
        self.sec_text.setVisible(vis_text)
        
        # Populate UI
        for section in self.sections:
            if section.isVisible():
                section.apply_state(clean_props)

    def _show_empty(self, show):
        self.lbl_empty.setVisible(show)
        for section in self.sections:
            section.setVisible(False)