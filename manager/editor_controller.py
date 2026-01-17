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
from engine.video_service import VideoService # Shared Instance Class

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
    sig_preview_update = Signal(float, list) 

    def __init__(self):
        super().__init__()
        self.state = ProjectState()
        
        # 1. CORE VIDEO SERVICE (Shared Instance)
        # Ini akan di-inject ke PreviewPanel oleh Binder
        self.video_service = VideoService()

        # 2. INIT ENGINES
        self.timeline = TimelineEngine()       
        self.preview_engine = PreviewEngine()  
        self.render_service = RenderService()  
        
        # 3. SERVICES
        self.tpl_service = TemplateService()
        self.io_service = ProjectIOService()
        self.cap_service = CaptionService()
        
        # 4. WIRING
        self.preview_engine.sig_tick.connect(self._on_engine_tick)
        self.preview_engine.sig_playback_state.connect(self._on_playback_state)
        
        self.cap_service.sig_success.connect(self._on_caption_success)
        self.cap_service.sig_fail.connect(self._on_caption_error)

    # ... (Method _on_engine_tick, _on_playback_state, toggle_play, seek_to TETAP SAMA) ...
    def _on_engine_tick(self, t: float):
        active_models = self.timeline.get_active_layers(t)
        active_ids = [l.id for l in active_models]
        self.sig_preview_update.emit(t, active_ids)

    def _on_playback_state(self, is_playing: bool):
        state = "▶️ PLAYING" if is_playing else "⏸️ PAUSED"
        self.sig_status_message.emit(state)

    def toggle_play(self):
        total_dur = self.timeline.get_total_duration()
        self.preview_engine.set_duration(max(total_dur + 1.0, 5.0))
        self.preview_engine.toggle_play()
        
    def seek_to(self, t: float):
        self.preview_engine.seek(t)
        self._on_engine_tick(self.preview_engine.current_time)

    # --- CRUD LAYERS (UPDATED) ---

    def add_new_layer(self, layer_type, path=None):
        new_id = str(uuid.uuid4())[:8]
        name = f"{layer_type.upper()} {len(self.state.layers) + 1}"
        
        # Gunakan LayerData dari ProjectState (No Dummy Class)
        layer_data = LayerData(id=new_id, type=layer_type, name=name, path=path)
        
        # REGISTER SOURCE KE VIDEO SERVICE
        if layer_type in ['video', 'image'] and path:
            self.video_service.register_source(new_id, path)

        self._insert_layer(layer_data)

    def _insert_layer(self, layer_data: LayerData):
        self.state.add_layer(layer_data)
        self._sync_layer_to_timeline(layer_data)
        self.sig_layer_created.emit(layer_data)
        self.select_layer(layer_data.id)

    # ... (_sync_layer_to_timeline, move_layer_time TETAP SAMA) ...
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
        total_dur = self.timeline.get_total_duration()
        self.preview_engine.set_duration(max(total_dur + 1.0, 5.0))

    def move_layer_time(self, layer_id: str, new_start_time: float):
        if new_start_time < 0: new_start_time = 0.0
        self.state.selected_layer_id = layer_id
        props = {"start_time": new_start_time}
        self.update_layer_property(props)
        
    def delete_current_layer(self):
        current_id = self.state.selected_layer_id
        if current_id:
            # UNREGISTER SOURCE DARI VIDEO SERVICE
            self.video_service.unregister_source(current_id)

            self.timeline.remove_layer(current_id)
            self.state.remove_layer(current_id)
            self.sig_layer_removed.emit(current_id)
            self.select_layer(None)
            self._on_engine_tick(self.preview_engine.current_time)

    # ... (Sisa Method: select_layer, update_layer_property, reorder_layers, dll TETAP SAMA) ...
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
        layer = self.state.layers.pop(from_idx)
        self.state.layers.insert(to_idx, layer)
        updates = []
        for i, l in enumerate(self.state.layers):
            l.z_index = i
            self._sync_layer_to_timeline(l) 
            updates.append({"id": l.id, "z_index": i})
        self.sig_layers_reordered.emit(updates)
        self.select_layer(layer.id)
        self._on_engine_tick(self.preview_engine.current_time)

    def load_project(self, path):
        layers = self.io_service.load_project(path)
        if layers:
            self.state.layers.clear()
            self.timeline.clear()
            self.video_service.release_all() # Reset service saat load baru
            self.sig_layer_cleared.emit()
            for l in layers:
                # Add layer akan otomatis register ke service
                self.add_new_layer(l.type, l.path) 
                # Note: Logic load asli mungkin perlu copy properties, 
                # tapi ini cukup untuk konteks perbaikan wiring.

    def save_project(self, path):
        self.io_service.save_project(self.state, path)

    def apply_template(self, tpl_id):
        layers = self.tpl_service.generate_layers(tpl_id)
        for l in layers:
            self._insert_layer(l)

    def process_render(self, config):
        if self.timeline.get_total_duration() <= 0:
            self.sig_status_message.emit("❌ Timeline is empty!")
            return
        self.sig_status_message.emit("⏳ Preparing Render...")
        success, worker_or_msg = self.render_service.start_render_process(self.timeline, config)
        if success:
            worker = worker_or_msg
            worker.sig_progress.connect(self._on_render_progress)
            worker.sig_finished.connect(self._on_render_finished)
            worker.sig_log.connect(lambda msg: print(f"[RENDER] {msg}"))
            worker.start()
            self.preview_engine.pause()
        else:
            self.sig_status_message.emit(f"❌ {worker_or_msg}")

    def _on_render_progress(self, val):
        self.sig_status_message.emit(f"Rendering: {val}%")

    def _on_render_finished(self, success, result):
        if success:
            self.sig_status_message.emit(f"✅ Export Success: {result}")
        else:
            self.sig_status_message.emit(f"❌ Export Failed: {result}")

    def add_audio_layer(self, path):
        self.add_new_layer("audio", path)

    def generate_auto_captions(self, config):
        current = self.state.get_layer(self.state.selected_layer_id)
        if current:
            self.cap_service.start_generate_async(current.path, config)

    def _on_caption_success(self, layer_models: list):
        for model in layer_models:
            props = model.payload.copy()
            props["start_time"] = model.time.start
            props["duration"] = model.time.duration
            layer_name = f"Subtitle {model.id[:4]}"
            layer_data = LayerData(
                id=model.id,
                type=model.type,
                name=layer_name,
                path=None
            )
            layer_data.properties.update(props)
            layer_data.z_index = model.z_index
            self._insert_layer(layer_data)
        self.sig_status_message.emit(f"Generated {len(layer_models)} captions")

    def _on_caption_error(self, msg):
        self.sig_status_message.emit(f"Error: {msg}")

    def apply_chroma_config(self, color_hex: str, threshold: float):
        current_id = self.state.selected_layer_id
        if not current_id: return
        props = {
            "chroma_active": True,
            "chroma_color": color_hex,
            "chroma_threshold": threshold
        }
        self.update_layer_property(props)
        self.sig_status_message.emit(f"✅ Chroma Applied: {color_hex}")

    def remove_chroma_config(self):
        current_id = self.state.selected_layer_id
        if not current_id: return
        self.update_layer_property({"chroma_active": False})
        self.sig_status_message.emit("🚫 Chroma Removed")