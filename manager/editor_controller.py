# manager/editor_controller.py

from PySide6.QtCore import QObject, Signal
import uuid
import os

# STATE & DATA
from manager.project_state import ProjectState, LayerData

# ENGINES
from manager.timeline.timeline_engine import TimelineEngine
from manager.timeline.layer_model import LayerModel
from manager.timeline.time_range import TimeRange
from engine.preview_engine import PreviewEngine
from engine.video_service import VideoService 

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
        
        self.current_frame = 0
        self.fps = 30.0
        
        self.video_service = VideoService()

        self.timeline = TimelineEngine()       
        self.preview_engine = PreviewEngine()  
        self.render_service = RenderService()  
        
        self.tpl_service = TemplateService()
        self.io_service = ProjectIOService()
        self.cap_service = CaptionService()
        
        self.preview_engine.sig_tick.connect(self._on_engine_tick)
        self.preview_engine.sig_playback_state.connect(self._on_playback_state)
        
        self.cap_service.sig_success.connect(self._on_caption_success)
        self.cap_service.sig_fail.connect(self._on_caption_error)

    # --- TIME LOGIC ---
    def time_to_frame(self, time_sec: float) -> int:
        if time_sec < 0: return 0
        return round(time_sec * self.fps)

    def frame_to_time(self, frame: int) -> float:
        if self.fps <= 0: return 0.0
        return frame / float(self.fps)

    # --- CORE LOOP ---
    def _on_engine_tick(self, t: float):
        self.current_frame = self.time_to_frame(t)
        clean_time = self.frame_to_time(self.current_frame)
        active_models = self.timeline.get_active_layers(clean_time)
        active_ids = [l.id for l in active_models]
        self.sig_preview_update.emit(clean_time, active_ids)

    def seek_to(self, t: float):
        target_frame = self.time_to_frame(t)
        self.current_frame = target_frame
        clean_time = self.frame_to_time(self.current_frame)
        self.preview_engine.seek(clean_time)
        
        active_models = self.timeline.get_active_layers(clean_time)
        active_ids = [l.id for l in active_models]
        self.sig_preview_update.emit(clean_time, active_ids)

    def toggle_play(self):
        total_dur = self.timeline.get_total_duration()
        self.preview_engine.set_duration(max(total_dur + 1.0, 5.0))
        self.preview_engine.toggle_play()

    def _on_playback_state(self, is_playing: bool):
        state = "▶️ PLAYING" if is_playing else "⏸️ PAUSED"
        self.sig_status_message.emit(state)

    # --- CRUD LAYERS ---
    def add_new_layer(self, layer_type, path=None):
        new_id = str(uuid.uuid4())[:8]
        name = f"{layer_type.upper()} {len(self.state.layers) + 1}"
        layer_data = LayerData(id=new_id, type=layer_type, name=name, path=path)
        if layer_type == 'text':
            layer_data.properties['text_content'] = "New Text"
        self._insert_layer(layer_data)

    def _insert_layer(self, layer_data: LayerData):
        if layer_data.type in ['video', 'image', 'audio'] and layer_data.path:
            if os.path.exists(layer_data.path):
                self.video_service.register_source(layer_data.id, layer_data.path)
                if layer_data.type == "video":
                    # Simple FPS detection hook
                    pass
            else:
                self.sig_status_message.emit(f"⚠️ File not found: {layer_data.path}")

        self.state.add_layer(layer_data)
        self._sync_layer_to_timeline(layer_data)
        self.sig_layer_created.emit(layer_data)
        self.select_layer(layer_data.id)
        
        start_t = float(layer_data.properties.get("start_time", 0.0))
        self.seek_to(start_t)
        self.sig_status_message.emit(f"✅ Layer Added: {layer_data.name}")

    def _sync_layer_to_timeline(self, layer_data: LayerData):
        self.timeline.remove_layer(layer_data.id)
        start = float(layer_data.properties.get("start_time", 0.0))
        duration = float(layer_data.properties.get("duration", 5.0))
        min_dur = 1.0 / self.fps if self.fps > 0 else 0.033
        if duration < min_dur: duration = min_dur

        model = LayerModel(
            id=layer_data.id,
            type=layer_data.type,
            time=TimeRange(start, start + duration),
            z_index=layer_data.z_index,
            payload=layer_data.properties
        )
        if layer_data.path:
            model.payload["path"] = layer_data.path
        self.timeline.add_layer(model)
        
        total_dur = self.timeline.get_total_duration()
        self.preview_engine.set_duration(max(total_dur + 1.0, 5.0))

    def move_layer_time(self, layer_id: str, new_start_time: float):
        if new_start_time < 0: new_start_time = 0.0
        frame_start = self.time_to_frame(new_start_time)
        clean_start_time = self.frame_to_time(frame_start)
        self.state.selected_layer_id = layer_id
        self.update_layer_property(layer_id, {"start_time": clean_start_time})
        self.seek_to(clean_start_time)

    def delete_current_layer(self):
        current_id = self.state.selected_layer_id
        if current_id:
            self.video_service.unregister_source(current_id)
            self.timeline.remove_layer(current_id)
            self.state.remove_layer(current_id)
            self.sig_layer_removed.emit(current_id)
            self.select_layer(None)
            clean_time = self.frame_to_time(self.current_frame)
            self.seek_to(clean_time)
            self.sig_status_message.emit("🗑️ Layer Deleted")

    # --- HELPERS ---
    def select_layer(self, layer_id):
        self.state.selected_layer_id = layer_id
        layer = self.state.get_layer(layer_id)
        self.sig_selection_changed.emit(layer)

    # ✅ FIXED: ROBUST PROPERTY UPDATE
    def update_layer_property(self, arg1, arg2=None, arg3=None):
        """
        Menangani berbagai format sinyal:
        1. (layer_id, dict) -> Dari Preview Panel
        2. (dict) -> Dari Panel Lama (Asumsi layer yang dipilih)
        3. (layer_id, key, value) -> Format Key-Value
        """
        layer_id = None
        new_props = {}

        # Deteksi Argumen
        if isinstance(arg1, dict):
            # Format: update_layer_property(props_dict)
            layer_id = self.state.selected_layer_id
            new_props = arg1
        elif isinstance(arg1, str) and isinstance(arg2, dict):
            # Format: update_layer_property(layer_id, props_dict)
            layer_id = arg1
            new_props = arg2
        elif isinstance(arg1, str) and isinstance(arg2, str):
            # Format: update_layer_property(layer_id, key, value)
            layer_id = arg1
            new_props = {arg2: arg3}
        else:
            # Fallback atau invalid
            return

        if not layer_id: return
        layer = self.state.get_layer(layer_id)
        if layer:
            layer.properties.update(new_props)
            if "start_time" in new_props or "duration" in new_props:
                self._sync_layer_to_timeline(layer)
            
            self.sig_property_changed.emit(layer_id, new_props)
            
            # Refresh Frame
            clean_time = self.frame_to_time(self.current_frame)
            self.seek_to(clean_time)

    def reorder_layers(self, from_idx: int, to_idx: int):
        if from_idx < 0 or to_idx < 0: return
        if from_idx >= len(self.state.layers) or to_idx >= len(self.state.layers): return
        layer = self.state.layers.pop(from_idx)
        self.state.layers.insert(to_idx, layer)
        updates = []
        for i, l in enumerate(self.state.layers):
            l.z_index = i
            self._sync_layer_to_timeline(l) 
            updates.append({"id": l.id, "z_index": i})
        self.sig_layers_reordered.emit(updates)
        self.select_layer(layer.id)
        clean_time = self.frame_to_time(self.current_frame)
        self.seek_to(clean_time)

    # --- RENDER ---
    def process_render(self, config):
        if self.timeline.get_total_duration() <= 0:
            self.sig_status_message.emit("❌ Timeline is empty!")
            return
            
        self.sig_status_message.emit("⏳ Preparing Render...")
        self.preview_engine.pause()
        
        # Panggil Service dengan nama yang BENAR
        success, worker_or_msg = self.render_service.start_render_process(self.timeline, config, self.video_service)
        
        if success:
            worker = worker_or_msg
            worker.sig_progress.connect(self._on_render_progress)
            worker.sig_finished.connect(self._on_render_finished)
            # Worker jalan otomatis karena sudah di-start di service
        else:
            self.sig_status_message.emit(f"❌ {worker_or_msg}")

    def _on_render_progress(self, val):
        self.sig_status_message.emit(f"Rendering: {val}%")

    def _on_render_finished(self, success, result):
        msg = f"✅ Export Success: {result}" if success else f"❌ Export Failed: {result}"
        self.sig_status_message.emit(msg)

    # --- OTHER SERVICES ---
    def load_project(self, path):
        self.sig_status_message.emit("📂 Loading Project...")
        layers = self.io_service.load_project(path)
        if layers is None:
            self.sig_status_message.emit("❌ Failed to load project")
            return
        self.preview_engine.pause()
        self.state.layers.clear()
        self.timeline.clear()
        self.video_service.release_all()
        self.sig_layer_cleared.emit()
        self.current_frame = 0
        for l in layers: self._insert_layer(l)
        self.seek_to(0.0)
        self.sig_status_message.emit("✅ Project Loaded")

    def save_project(self, path=None):
        if not path: return
        if self.io_service.save_project(self.state, path):
            self.sig_status_message.emit(f"💾 Saved: {os.path.basename(path)}")
        else:
            self.sig_status_message.emit("❌ Save Failed")

    def apply_template(self, tpl_id):
        layers = self.tpl_service.generate_layers(tpl_id)
        for l in layers: self._insert_layer(l)

    def add_audio_layer(self, path):
        self.add_new_layer("audio", path)

    def generate_auto_captions(self, config):
        current = self.state.get_layer(self.state.selected_layer_id)
        if current and current.path:
            self.sig_status_message.emit("🎙️ Generating Captions...")
            self.cap_service.start_generate_async(current.path, config)
        else:
            self.sig_status_message.emit("⚠️ Select video layer first.")

    def _on_caption_success(self, layer_models: list):
        for model in layer_models:
            layer_data = LayerData(
                id=model.id, type="text", name="Subtitle", path=None, properties=model.payload
            )
            layer_data.properties["start_time"] = model.time.start
            layer_data.properties["duration"] = model.time.duration
            self._insert_layer(layer_data)
        self.sig_status_message.emit(f"✅ Generated {len(layer_models)} captions")

    def _on_caption_error(self, msg):
        self.sig_status_message.emit(f"❌ Caption Error: {msg}")

    def apply_chroma_config(self, color_hex: str, threshold: float):
        self.update_layer_property(self.state.selected_layer_id, {
            "chroma_active": True, "chroma_color": color_hex, "chroma_threshold": threshold
        })

    def remove_chroma_config(self):
        self.update_layer_property(self.state.selected_layer_id, {"chroma_active": False})