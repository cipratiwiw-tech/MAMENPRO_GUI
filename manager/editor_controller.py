# manager/editor_controller.py
from PySide6.QtCore import QObject, Signal
from manager.project_state import ProjectState, LayerData
import uuid

# SERVICES
from manager.services.template_service import TemplateService
from manager.services.render_service import RenderService
from manager.services.project_io_service import ProjectIOService # [BARU]

class EditorController(QObject):
    # Signals (Tetap sama)
    sig_layer_created = Signal(object)
    sig_layer_removed = Signal(str)
    sig_layer_cleared = Signal() # [BARU] Signal untuk reset canvas saat load new project
    sig_property_changed = Signal(str, dict)
    sig_selection_changed = Signal(object)
    sig_status_message = Signal(str)
    # [BARU] Signal khusus reorder: mengirim list dict {id: str, z_index: int}
    sig_layers_reordered = Signal(list)

    def __init__(self):
        super().__init__()
        self.state = ProjectState()
        
        # REKRUT PEKERJA
        self.tpl_service = TemplateService()
        self.render_service = RenderService()
        self.io_service = ProjectIOService() # [BARU]

    # --- BAGIAN 1: LAYER CRUD (Logic Inti) ---
    def add_new_layer(self, layer_type, path=None):
        new_id = str(uuid.uuid4())[:8]
        name = f"{layer_type.upper()} {len(self.state.layers) + 1}"
        layer = LayerData(id=new_id, type=layer_type, name=name, path=path)
        self._insert_layer(layer)

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

    # --- BAGIAN 2: DELEGASI TUGAS (Pakai Service) ---

    def apply_template(self, template_id: str):
        """DELEGATOR: Minta service buatkan layer, lalu Controller masukkan ke state."""
        print(f"[CONTROLLER] Delegating template creation: {template_id}")
        
        # 1. Service kerja
        new_layers = self.tpl_service.generate_layers(template_id)
        
        # 2. Controller update state
        for layer in new_layers:
            self._insert_layer(layer)
            
        self.sig_status_message.emit(f"Template {template_id} applied.")

    def process_render(self, render_config: dict):
        """DELEGATOR: Minta service validasi & render."""
        # 1. Service Validasi
        is_valid, msg = self.render_service.validate_config(render_config)
        
        if not is_valid:
            print(f"[CONTROLLER] Render Rejected: {msg}")
            self.sig_status_message.emit(f"❌ Error: {msg}")
            return

        # 2. Service Eksekusi
        self.render_service.start_render_process(self.state, render_config)
        self.sig_status_message.emit("✅ Render Started...")

    # --- PROJECT IO (DELEGATION) ---
    def save_project(self, file_path: str):
        if not file_path: return
        
        self.sig_status_message.emit("Saving project...")
        success = self.io_service.save_project(self.state, file_path)
        
        if success:
            self.sig_status_message.emit(f"✅ Project saved: {file_path}")
        else:
            self.sig_status_message.emit("❌ Failed to save project!")

    def load_project(self, file_path: str):
        if not file_path: return
        
        self.sig_status_message.emit("Loading project...")
        new_layers = self.io_service.load_project(file_path)
        
        if new_layers:
            # 1. Bersihkan State Lama
            self.state.layers.clear()
            self.sig_layer_cleared.emit() # UI harus dengar ini untuk clear visual
            
            # 2. Masukkan Data Baru
            for layer in new_layers:
                self._insert_layer(layer) # Reuse method internal
                
            self.sig_status_message.emit(f"✅ Project loaded: {len(new_layers)} layers")
        else:
            self.sig_status_message.emit("❌ Failed to load project or empty.")
            
    # Helper Internal
    def _insert_layer(self, layer):
        self.state.add_layer(layer)
        self.sig_layer_created.emit(layer)
        self.select_layer(layer.id)
        
    # --- REORDER LOGIC ---
    def reorder_layers(self, from_idx: int, to_idx: int):
        """
        Memindahkan layer dalam list state dan update Z-Index.
        """
        if from_idx < 0 or to_idx < 0: return
        if from_idx >= len(self.state.layers) or to_idx >= len(self.state.layers): return
        if from_idx == to_idx: return

        print(f"[CONTROLLER] Reordering layer {from_idx} -> {to_idx}")

        # 1. Pindahkan item di List Python
        layer = self.state.layers.pop(from_idx)
        self.state.layers.insert(to_idx, layer)

        # 2. Update Z-Index untuk SEMUA layer (agar konsisten)
        # Index 0 = Z 0 (Paling Bawah)
        updates = []
        for i, l in enumerate(self.state.layers):
            l.z_index = i
            # Kita kumpulkan data perubahan untuk dikirim ke UI
            updates.append({"id": l.id, "z_index": i})

        # 3. Emit Signal Spesifik
        self.sig_layers_reordered.emit(updates)
        
        # 4. Opsional: Reselect item yang dipindah
        self.select_layer(layer.id)