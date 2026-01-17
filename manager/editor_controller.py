# manager/editor_controller.py
from PySide6.QtCore import QObject, Signal
import uuid

# STATE & DATA
from manager.project_state import ProjectState, LayerData

# ENGINES
from manager.timeline.timeline_engine import TimelineEngine
from manager.timeline.layer_model import LayerModel
from manager.timeline.time_range import TimeRange
from engine.preview_engine import PreviewEngine
from engine.render_engine import RenderEngine 

# SERVICES
from manager.services.template_service import TemplateService
from manager.services.render_service import RenderService
from manager.services.project_io_service import ProjectIOService
from manager.services.caption_service import CaptionService

class EditorController(QObject):
    # Signals UI Updates
    sig_layer_created = Signal(object)
    sig_layer_removed = Signal(str)
    sig_layer_cleared = Signal()
    sig_property_changed = Signal(str, dict)
    sig_selection_changed = Signal(object)
    sig_status_message = Signal(str)
    sig_layers_reordered = Signal(list)
    
    # [ORCHESTRATOR SIGNAL] 
    # Mengirim Waktu & List ID Layer yang HARUS tampil saat ini
    sig_preview_update = Signal(float, list) 

    def __init__(self):
        super().__init__()
        self.state = ProjectState()
        
        # 1. INIT ENGINES
        self.timeline = TimelineEngine()       # Logic: Siapa aktif?
        self.preview_engine = PreviewEngine()  # Logic: Sekarang jam berapa?
        self.render_service = RenderService()  # Logic: Export video
        
        # 2. SERVICES
        self.tpl_service = TemplateService()
        self.io_service = ProjectIOService()
        self.cap_service = CaptionService()
        
        # 3. WIRING (Controller mendengar detak jantung Engine)
        self.preview_engine.sig_tick.connect(self._on_engine_tick)
        self.preview_engine.sig_playback_state.connect(self._on_playback_state)
        
        # Async Service Wiring
        self.cap_service.sig_success.connect(self._on_caption_success)
        self.cap_service.sig_fail.connect(self._on_caption_error)

    # =========================================================================
    # CORE ORCHESTRATION (Jantung Aplikasi)
    # =========================================================================
    
    def _on_engine_tick(self, t: float):
        """
        Satu-satunya tempat di mana Waktu + Logic Timeline + Render bertemu.
        """
        # 1. Tanya Timeline: "Siapa yang aktif di detik t?"
        active_models = self.timeline.get_active_layers(t)
        
        # 2. Ambil ID saja untuk View (View akan hide layer yang tidak ada di list ini)
        active_ids = [l.id for l in active_models]
        
        # 3. Perintahkan View/Binder untuk Render (Update Visual)
        self.sig_preview_update.emit(t, active_ids)

    def _on_playback_state(self, is_playing: bool):
        state = "▶️ PLAYING" if is_playing else "⏸️ PAUSED"
        self.sig_status_message.emit(state)

    def toggle_play(self):
        # [UPDATED] Mengambil durasi langsung dari Timeline Engine
        # Tambahkan buffer sedikit (misal 1 detik) agar tidak berhenti mendadak pas di frame terakhir
        total_dur = self.timeline.get_total_duration()
        self.preview_engine.set_duration(max(total_dur + 1.0, 5.0))
        self.preview_engine.toggle_play()

    # --- SYNC LOGIC ---

    def add_new_layer(self, layer_type, path=None):
        new_id = str(uuid.uuid4())[:8]
        name = f"{layer_type.upper()} {len(self.state.layers) + 1}"
        layer_data = LayerData(id=new_id, type=layer_type, name=name, path=path)
        self._insert_layer(layer_data)

    def _insert_layer(self, layer_data: LayerData):
        self.state.add_layer(layer_data)
        self._sync_layer_to_timeline(layer_data)
        self.sig_layer_created.emit(layer_data)
        self.select_layer(layer_data.id)

    def _sync_layer_to_timeline(self, layer_data: LayerData):
        self.timeline.remove_layer(layer_data.id)
        
        start = float(layer_data.properties.get("start_time", 0.0))
        duration = float(layer_data.properties.get("duration", 5.0))
        
        model = LayerModel(
            id=layer_data.id,
            type=layer_data.type,
            time=TimeRange(start, start + duration),
            z_index=layer_data.z_index,
            payload={"path": layer_data.path}
        )
        self.timeline.add_layer(model)
        
        # [OPTIONAL] Update durasi preview engine saat ada layer baru/berubah
        # agar seek bar (kalau ada) langsung menyesuaikan panjang timeline
        total_dur = self.timeline.get_total_duration()
        self.preview_engine.set_duration(max(total_dur + 1.0, 5.0))

    def delete_current_layer(self):
        current_id = self.state.selected_layer_id
        if current_id:
            self.timeline.remove_layer(current_id)
            self.state.remove_layer(current_id)
            self.sig_layer_removed.emit(current_id)
            self.select_layer(None)
            self._on_engine_tick(self.preview_engine.current_time)

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
            if "start_time" in new_props or "duration" in new_props:
                self._sync_layer_to_timeline(layer)
            self.sig_property_changed.emit(current_id, new_props)
            self._on_engine_tick(self.preview_engine.current_time)
        
    def reorder_layers(self, from_idx: int, to_idx: int):
        if from_idx < 0 or to_idx < 0: return
        if from_idx >= len(self.state.layers) or to_idx >= len(self.state.layers): return
        if from_idx == to_idx: return

        # Swap di list state
        layer = self.state.layers.pop(from_idx)
        self.state.layers.insert(to_idx, layer)

        updates = []
        for i, l in enumerate(self.state.layers):
            l.z_index = i
            # SYNC Timeline: Update Z-Index di Engine
            self._sync_layer_to_timeline(l) 
            updates.append({"id": l.id, "z_index": i})

        self.sig_layers_reordered.emit(updates)
        self.select_layer(layer.id)
        
        # Force refresh visual tumpukan
        self._on_engine_tick(self.preview_engine.current_time)

    # --- WRAPPERS (Sama seperti sebelumnya) ---
    def load_project(self, path):
        layers = self.io_service.load_project(path)
        if layers:
            self.state.layers.clear()
            self.timeline.clear() # Reset engine
            self.sig_layer_cleared.emit()
            for l in layers:
                self._insert_layer(l)

    def save_project(self, path):
        self.io_service.save_project(self.state, path)

    def apply_template(self, tpl_id):
        layers = self.tpl_service.generate_layers(tpl_id)
        for l in layers:
            self._insert_layer(l)

    def process_render(self, config):
        # Render Service pakai logic sendiri (threading), jadi tidak perlu on_tick
        self.render_service.start_render_process(self.state, config)

    def add_audio_layer(self, path):
        self.add_new_layer("audio", path)

    def generate_auto_captions(self, config):
        self.cap_service.start_generate_async(self.state.get_layer(self.state.selected_layer_id).path, config)

    def _on_caption_success(self, new_layers):
        for l in new_layers:
            self._insert_layer(l)
        self.sig_status_message.emit(f"Generated {len(new_layers)} captions")

    def _on_caption_error(self, msg):
        self.sig_status_message.emit(f"Error: {msg}")

    # CHROMA WRAPPERS (Simple Property Update)
    def apply_chroma_config(self, color, thresh):
        self.update_layer_property({"chroma_active": True, "chroma_color": color, "chroma_threshold": thresh})
        
    def remove_chroma_config(self):
        self.update_layer_property({"chroma_active": False})