# manager/editor_controller.py
from PySide6.QtCore import QObject, Signal
from manager.project_state import ProjectState, LayerData
import uuid

class EditorController(QObject):
    # --- OUTPUT SIGNALS (Event yang ditembakkan ke luar) ---
    # UI harus connect ke sini. Controller tidak peduli siapa yang connect.
    sig_layer_created = Signal(object)      # Mengirim object LayerData
    sig_layer_removed = Signal(str)         # Mengirim ID layer
    sig_property_changed = Signal(str, dict)# ID, dict perubahan
    sig_selection_changed = Signal(object)  # LayerData (bisa None)

    def __init__(self):
        super().__init__()
        self.state = ProjectState()

    # --- INPUT ACTIONS (Dipanggil oleh UI) ---
    
    def add_new_layer(self, layer_type, path=None):
        """Logic Bisnis: Membuat data layer baru"""
        new_id = str(uuid.uuid4())[:8]
        name = f"{layer_type.upper()} {len(self.state.layers) + 1}"
        
        # 1. Buat Data Murni
        layer = LayerData(id=new_id, type=layer_type, name=name, path=path)
        
        # 2. Update State Internal
        self.state.add_layer(layer)
        
        # 3. Kabari Dunia Luar (Emit Signal)
        self.sig_layer_created.emit(layer)
        
        # Auto-select layer yang baru dibuat
        self.select_layer(new_id)

    def select_layer(self, layer_id):
        """Logic Bisnis: Mengubah selection state"""
        self.state.selected_layer_id = layer_id
        layer = self.state.get_layer(layer_id)
        self.sig_selection_changed.emit(layer)

    def update_layer_property(self, new_props: dict):
        """Logic Bisnis: Update properti data"""
        current_id = self.state.selected_layer_id
        if not current_id: return

        layer = self.state.get_layer(current_id)
        if layer:
            layer.properties.update(new_props)
            self.sig_property_changed.emit(current_id, new_props)

    def delete_current_layer(self):
        current_id = self.state.selected_layer_id
        if current_id:
            self.state.remove_layer(current_id)
            self.sig_layer_removed.emit(current_id)
            self.select_layer(None)