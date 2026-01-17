# gui/right_panel/setting_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PySide6.QtCore import Signal, Qt

# Import Pure Sections
from .sections.transform_section import TransformSection
from .sections.appearance_section import AppearanceSection

class StateAdapter:
    """
    Jembatan antara LEGACY BACKEND (Flat Dict) dan MODERN UI (Nested Dict).
    Class ini akan dihapus setelah Controller & ProjectState direfactor total.
    """
    @staticmethod
    def to_ui_structure(flat_props: dict) -> dict:
        """Flat (x, y, scale) -> Nested (transform.position.x)"""
        return {
            "transform": {
                "position": {
                    "x": flat_props.get("x", 0),
                    "y": flat_props.get("y", 0)
                },
                "scale": {
                    "x": flat_props.get("scale_x", flat_props.get("scale", 100)),
                    "y": flat_props.get("scale_y", flat_props.get("scale", 100))
                },
                "rotation": flat_props.get("rotation", 0),
                "anchor": {
                    "x": flat_props.get("anchor_x", 0.5), # Standard Normalized
                    "y": flat_props.get("anchor_y", 0.5)
                }
            },
            "appearance": {
                "opacity": flat_props.get("opacity", 1.0),
                "blend_mode": flat_props.get("blend_mode", "Normal")
            }
        }

    @staticmethod
    def to_legacy_update(path: str, value) -> dict:
        """Path (transform.position.x) -> Flat ({x: 10})"""
        # Mapping Table
        map_table = {
            "transform.position.x": "x",
            "transform.position.y": "y",
            "transform.scale.x": "scale_x",
            "transform.scale.y": "scale_y",
            "transform.rotation": "rotation",
            "transform.anchor.x": "anchor_x",
            "transform.anchor.y": "anchor_y",
            "appearance.opacity": "opacity",
            "appearance.blend_mode": "blend_mode"
        }
        
        if path in map_table:
            return {map_table[path]: value}
        return {}

class SettingPanel(QWidget):
    # Modern Signal (Future Proof)
    sig_property_changed = Signal(str, object) 
    # Legacy Signal (Keep Alive for Current Controller)
    sig_property_update = Signal(dict)

    def __init__(self, parent=None):
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
        self.sec_appearance = AppearanceSection()
        
        self._register_section(self.sec_transform)
        self._register_section(self.sec_appearance)

    def _register_section(self, section):
        self.container_layout.addWidget(section)
        self.sections.append(section)
        section.hide()
        # Orchestrator mendengarkan semua perubahan dari Section
        section.sig_edit_changed.connect(self._on_section_change)

    def _on_section_change(self, path, value):       
        print("[UI]", path, value)
        # 1. Emit Modern (Path Based)
        self.sig_property_changed.emit(path, value)
        
        # 2. Convert to Legacy & Emit (Untuk Controller saat ini)
        legacy_payload = StateAdapter.to_legacy_update(path, value)
        if legacy_payload:
            self.sig_property_update.emit(legacy_payload)

    def set_values(self, layer_data):
        if not layer_data:
            self._show_empty(True)
            return

        self._show_empty(False)
        
        # --- ADAPTER IN ACTION ---
        # Mengubah data kotor (Flat) menjadi data bersih (Nested) sebelum masuk UI
        # UI tidak tahu data aslinya Flat.
        flat_props = layer_data.properties
        clean_props = StateAdapter.to_ui_structure(flat_props)
        
        l_type = layer_data.type
        
        # Visibility Logic
        self.sec_transform.setVisible(l_type in ['video', 'image', 'text', 'shape', 'caption'])
        self.sec_appearance.setVisible(l_type in ['video', 'image', 'text', 'shape'])
        
        # Populate UI
        for section in self.sections:
            if section.isVisible():
                section.apply_state(clean_props)

    def _show_empty(self, show):
        self.lbl_empty.setVisible(show)
        for section in self.sections:
            section.setVisible(False)
            

