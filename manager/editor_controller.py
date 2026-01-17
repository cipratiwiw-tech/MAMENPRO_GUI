# manager/editor_controller.py
from PySide6.QtCore import QObject, Signal
from manager.project_state import ProjectState, LayerData
import uuid

# Import Services Baru
from manager.services.template_service import TemplateService
from manager.services.render_service import RenderService

class EditorController(QObject):
    # Signals
    sig_layer_created = Signal(object)
    sig_layer_removed = Signal(str)
    sig_property_changed = Signal(str, dict)
    sig_selection_changed = Signal(object)
    
    # Signal System (Error/Status)
    sig_system_message = Signal(str) # Bisa untuk toast error/info

    def __init__(self):
        super().__init__()
        self.state = ProjectState()
        
        # Init Services
        self.tpl_service = TemplateService()
        self.render_service = RenderService()

    # --- LAYER CRUD ---
    def add_new_layer(self, layer_type, path=None):
        new_id = str(uuid.uuid4())[:8]
        name = f"{layer_type.upper()} {len(self.state.layers) + 1}"
        
        layer = LayerData(id=new_id, type=layer_type, name=name, path=path)
        self._insert_layer_to_state(layer)

    def select_layer(self, layer_id):
        self.state.selected_layer_id = layer_id
        layer = self.state.get_layer(layer_id)
        self.sig_selection_changed.emit(layer)

    def update_layer_property(self, new_props: dict):
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

    # --- FEATURE DELEGATION (REFACTORED) ---

    def apply_template(self, template_id: str):
        """
        Controller tidak perlu tahu detail template.
        Dia minta Service buatkan layer, lalu Controller memasukkannya ke State.
        """
        print(f"[CONTROLLER] Requesting template: {template_id}")
        
        # 1. Minta Service generate layers
        new_layers = self.tpl_service.generate_layers_from_template(template_id)
        
        # 2. Masukkan ke State & Emit Signal satu per satu
        for layer in new_layers:
            self._insert_layer_to_state(layer)
            
    def process_render_request(self, render_config: dict):
        """
        Controller delegasi ke RenderService.
        """
        # 1. Validasi via Service
        is_valid, err_msg = self.render_service.validate_render_config(render_config)
        
        if not is_valid:
            print(f"[ERROR] Render Validation Failed: {err_msg}")
            self.sig_system_message.emit(f"Render Error: {err_msg}")
            return

        # 2. Eksekusi Render
        self.render_service.start_render(self.state, render_config)
        self.sig_system_message.emit("Rendering Started...")

    # --- HELPER INTERNAL ---
    def _insert_layer_to_state(self, layer: LayerData):
        """Helper untuk add + emit agar DRY (Don't Repeat Yourself)"""
        self.state.add_layer(layer)
        self.sig_layer_created.emit(layer)
        self.select_layer(layer.id)