# manager/editor_controller.py
from PySide6.QtCore import QObject, Signal
from manager.project_state import ProjectState, LayerData
import uuid

# IMPORT ENGINE
from engine.preview_engine import PreviewEngine # [BARU]

# SERVICES
from manager.services.template_service import TemplateService
from manager.services.render_service import RenderService
from manager.services.project_io_service import ProjectIOService
from manager.services.caption_service import CaptionService

class EditorController(QObject):
    # Signals
    sig_layer_created = Signal(object)
    sig_layer_removed = Signal(str)
    sig_layer_cleared = Signal()
    sig_property_changed = Signal(str, dict)
    sig_selection_changed = Signal(object)
    sig_status_message = Signal(str)
    sig_layers_reordered = Signal(list)
    
    # [BARU] Signal Waktu untuk UI
    sig_time_updated = Signal(float)    

    def __init__(self):
        super().__init__()
        self.state = ProjectState()
        
        # ENGINE TIMELINE
        self.preview_engine = PreviewEngine(fps=30)
        # Sambungkan detak jantung engine ke Controller
        self.preview_engine.sig_time_changed.connect(self._on_engine_tick)
        
        # SERVICES
        self.tpl_service = TemplateService()
        self.render_service = RenderService()
        self.io_service = ProjectIOService()
        self.cap_service = CaptionService()
        
        # Connect Async Service
        self.cap_service.sig_success.connect(self._on_caption_success)
        self.cap_service.sig_fail.connect(self._on_caption_error)

    # [BARU] Handler Detak Engine
    def _on_engine_tick(self, t: float):
        # Teruskan ke UI (PreviewPanel akan mendengarkan ini via Binder)
        self.sig_time_updated.emit(t)

    # [BARU] Kontrol Playback (Bisa dipanggil dari tombol Play nanti)
    def toggle_play(self):
        # Update durasi proyek berdasarkan layer terakhir selesai
        max_duration = 0
        for layer in self.state.layers:
            end = layer.properties.get("start_time", 0) + layer.properties.get("duration", 0)
            if end > max_duration:
                max_duration = end
        
        # Set durasi ke engine agar tau kapan stop/loop
        self.preview_engine.set_duration(max_duration if max_duration > 0 else 10.0)
        self.preview_engine.toggle_play()
        
        state = "Playing" if self.preview_engine.timer.isActive() else "Paused"
        self.sig_status_message.emit(f"⏯️ {state}")

    # --- BAGIAN 1: LAYER CRUD ---
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

    # Helper Internal
    def _insert_layer(self, layer):
        self.state.add_layer(layer)
        self.sig_layer_created.emit(layer)
        self.select_layer(layer.id)

    # --- BAGIAN 2: DELEGASI TUGAS ---
    def apply_template(self, template_id: str):
        print(f"[CONTROLLER] Delegating template creation: {template_id}")
        new_layers = self.tpl_service.generate_layers(template_id)
        for layer in new_layers:
            self._insert_layer(layer)
        self.sig_status_message.emit(f"Template {template_id} applied.")

    def process_render(self, render_config: dict):
        is_valid, msg = self.render_service.validate_config(render_config)
        if not is_valid:
            self.sig_status_message.emit(f"❌ Error: {msg}")
            return
        self.render_service.start_render_process(self.state, render_config)
        self.sig_status_message.emit("✅ Render Started...")

    # --- PROJECT IO ---
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
            self.state.layers.clear()
            self.sig_layer_cleared.emit()
            for layer in new_layers:
                self._insert_layer(layer)
            self.sig_status_message.emit(f"✅ Project loaded: {len(new_layers)} layers")
        else:
            self.sig_status_message.emit("❌ Failed to load project or empty.")

    # --- REORDER ---
    def reorder_layers(self, from_idx: int, to_idx: int):
        if from_idx < 0 or to_idx < 0: return
        if from_idx >= len(self.state.layers) or to_idx >= len(self.state.layers): return
        if from_idx == to_idx: return

        print(f"[CONTROLLER] Reordering layer {from_idx} -> {to_idx}")
        layer = self.state.layers.pop(from_idx)
        self.state.layers.insert(to_idx, layer)

        updates = []
        for i, l in enumerate(self.state.layers):
            l.z_index = i
            updates.append({"id": l.id, "z_index": i})

        self.sig_layers_reordered.emit(updates)
        self.select_layer(layer.id)

    # --- AUDIO ---
    def add_audio_layer(self, path: str):
        self.add_new_layer("audio", path)

    # --- CHROMA ---
    def apply_chroma_config(self, color_hex: str, threshold: float):
        current_id = self.state.selected_layer_id
        if not current_id: 
            self.sig_status_message.emit("⚠️ Select a layer first!")
            return
        
        updates = {
            "chroma_active": True,
            "chroma_color": color_hex,
            "chroma_threshold": threshold
        }
        self.update_layer_property(updates)
        self.sig_status_message.emit(f"✅ Chroma applied: {color_hex}")

    def remove_chroma_config(self):
        current_id = self.state.selected_layer_id
        if current_id:
            self.update_layer_property({"chroma_active": False})
            self.sig_status_message.emit("🚫 Chroma removed")

    # --- CAPTION LOGIC (UPDATED ASYNC) ---
    def generate_auto_captions(self, config: dict):
        """
        Orkestrator Async:
        Memicu Worker dan segera kembali agar UI tidak macet.
        """
        current_id = self.state.selected_layer_id
        if not current_id:
            self.sig_status_message.emit("⚠️ Select a video/audio layer first!")
            return

        layer = self.state.get_layer(current_id)
        if not layer or not layer.path:
            self.sig_status_message.emit("⚠️ Layer has no media file.")
            return

        # 1. UI Feedback Langsung
        self.sig_status_message.emit("⏳ AI Processing Started... Please wait.")
        
        # 2. Panggil Service ASYNC (Void return)
        self.cap_service.start_generate_async(layer.path, config)

    # [BARU] Handler saat Sukses (Callback)
    def _on_caption_success(self, new_layers):
        if not new_layers:
            self.sig_status_message.emit("❌ AI finished but found no speech.")
            return

        # Masukkan ke State
        for l in new_layers:
            self._insert_layer(l)
            
        count = len(new_layers)
        self.sig_status_message.emit(f"✅ AI Done: Generated {count} captions.")
        
        # [FIX PENTING] Paksa UI untuk refresh visibility berdasarkan waktu saat ini (t=0)
        # Ini akan menyembunyikan caption yang start_time-nya > 0
        current_t = self.preview_engine.current_time
        self.sig_time_updated.emit(current_t)

    # Tambahkan method ini jika belum ada (untuk tombol Play nanti)
    def toggle_play(self):
        # Hitung durasi proyek otomatis
        max_duration = 0
        for layer in self.state.layers:
            # Ambil properti dengan aman
            start = layer.properties.get("start_time", 0)
            dur = layer.properties.get("duration", 5)
            if start + dur > max_duration:
                max_duration = start + dur
        
        # Set durasi engine (minimal 10 detik biar gak kaget)
        self.preview_engine.set_duration(max(max_duration, 10.0))
        
        # Toggle
        self.preview_engine.toggle_play()
        
        # Update Status Bar
        is_playing = self.preview_engine.timer.isActive()
        status = "▶️ PLAYING" if is_playing else "⏸️ PAUSED"
        self.sig_status_message.emit(status)

    # [BARU] Handler saat Error
    def _on_caption_error(self, err_msg):
        print(f"[CONTROLLER ERROR] Caption failed: {err_msg}")
        self.sig_status_message.emit(f"❌ AI Error: {err_msg}")