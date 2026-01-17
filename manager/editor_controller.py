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
    # Param 1: Clean Time (float derived from frame), Param 2: Active IDs
    sig_preview_update = Signal(float, list) 

    def __init__(self):
        super().__init__()
        self.state = ProjectState()
        
        # 1. CORE SOURCE OF TRUTH (FRAME INDEX & FPS)
        self.current_frame = 0
        self.fps = 30.0  # Default fallback, dynamic source
        
        # 2. CORE VIDEO SERVICE (Shared Instance)
        self.video_service = VideoService()

        # 3. INIT ENGINES
        self.timeline = TimelineEngine()       
        self.preview_engine = PreviewEngine()  
        self.render_service = RenderService()  
        
        # 4. SERVICES
        self.tpl_service = TemplateService()
        self.io_service = ProjectIOService()
        self.cap_service = CaptionService()
        
        # 5. WIRING
        self.preview_engine.sig_tick.connect(self._on_engine_tick)
        self.preview_engine.sig_playback_state.connect(self._on_playback_state)
        
        self.cap_service.sig_success.connect(self._on_caption_success)
        self.cap_service.sig_fail.connect(self._on_caption_error)

    # =========================================================================
    # 🧠 THE GOLDEN PRINCIPLES (TIME <-> FRAME)
    # =========================================================================
    
    def time_to_frame(self, time_sec: float) -> int:
        """Mengubah waktu kotor (input user/timer) menjadi Frame Index (kebenaran)."""
        if time_sec < 0: return 0
        return round(time_sec * self.fps) # <--- Pakai self.fps

    def frame_to_time(self, frame: int) -> float:
        """Menghitung waktu bersih berdasarkan Frame Index."""
        if self.fps <= 0: return 0.0
        return frame / float(self.fps) # <--- Pakai self.fps

    # =========================================================================
    # CORE LOOP (FRAME DRIVEN)
    # =========================================================================

    def _on_engine_tick(self, t: float):
        """
        Handler saat PreviewEngine 'berdetak'.
        Kita bajak waktunya, konversi ke Frame Index, baru broadcast.
        """
        # 1. Update Truth (Frame Index)
        self.current_frame = self.time_to_frame(t)
        
        # 2. Derive Clean Time (Untuk UI & Timeline Query)
        # Ini menjamin waktu selalu kelipatan sempurna (contoh: 0.033333, 0.066666)
        clean_time = self.frame_to_time(self.current_frame)
        
        # 3. Query Timeline dengan Waktu Bersih
        active_models = self.timeline.get_active_layers(clean_time)
        active_ids = [l.id for l in active_models]
        
        # 4. Broadcast (VideoService & UI akan terima waktu yang 100% konsisten)
        self.sig_preview_update.emit(clean_time, active_ids)

    def seek_to(self, t: float):
        """
        Scrubbing Logic: User minta waktu T (float).
        Kita bulatkan ke Frame terdekat, lalu paksa Engine ke sana.
        """
        # 1. Konversi Input User -> Frame Truth
        target_frame = self.time_to_frame(t)
        
        # 2. Update State
        self.current_frame = target_frame
        
        # 3. Hitung Waktu Bersih
        clean_time = self.frame_to_time(self.current_frame)
        
        # 4. Paksa Engine sinkron ke Waktu Bersih
        self.preview_engine.seek(clean_time)
        
        # 5. Force Visual Update (Manual Tick)
        # Gunakan logika frame yang sama persis
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

    # =========================================================================
    # CRUD LAYERS
    # =========================================================================

    def add_new_layer(self, layer_type, path=None):
        new_id = str(uuid.uuid4())[:8]
        name = f"{layer_type.upper()} {len(self.state.layers) + 1}"
        
        layer_data = LayerData(id=new_id, type=layer_type, name=name, path=path)
        
        if layer_type == 'text':
            layer_data.properties['text_content'] = "New Text"
        
        self._insert_layer(layer_data)

    def _insert_layer(self, layer_data: LayerData):
        # 1. Register Source
        if layer_data.type in ['video', 'image', 'audio'] and layer_data.path:
            if os.path.exists(layer_data.path):
                # Register media ke VideoService
                self.video_service.register_source(layer_data.id, layer_data.path)

                # Jika video, ambil FPS dari media (dinamis)
                if layer_data.type == "video":
                    get_fps = getattr(self.video_service, "get_fps", None)
                    if callable(get_fps):
                        detected_fps = get_fps(layer_data.id)
                        if detected_fps and detected_fps > 0:
                            self.fps = float(detected_fps)
            else:
                # Path ada tapi file tidak ditemukan
                self.sig_status_message.emit(f"⚠️ File not found: {layer_data.path}")

        # 2. Update State
        self.state.add_layer(layer_data)

        # 3. Update Timeline
        self._sync_layer_to_timeline(layer_data)

        # 4. Notify UI
        self.sig_layer_created.emit(layer_data)
        self.select_layer(layer_data.id)

        # 5. FORCE PREVIEW (Using Frame Logic)
        start_t = float(layer_data.properties.get("start_time", 0.0))
        self.seek_to(start_t)

        self.sig_status_message.emit(f"✅ Layer Added: {layer_data.name}")

    def _sync_layer_to_timeline(self, layer_data: LayerData):
        self.timeline.remove_layer(layer_data.id)
        
        start = float(layer_data.properties.get("start_time", 0.0))
        duration = float(layer_data.properties.get("duration", 5.0))
        
        # Pastikan durasi minimal 1 frame (Safe Division)
        min_dur = 1.0 / self.fps if self.fps > 0 else 0.033
        if duration < min_dur: duration = min_dur

        model = LayerModel(
            # ... (kode pembuatan model sama persis) ...
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
        
        # Snap posisi layer ke frame grid juga agar rapi
        frame_start = self.time_to_frame(new_start_time)
        clean_start_time = self.frame_to_time(frame_start)
        
        self.state.selected_layer_id = layer_id
        props = {"start_time": clean_start_time}
        self.update_layer_property(props)
        
        # Instant feedback
        self.seek_to(clean_start_time)

    def delete_current_layer(self):
        current_id = self.state.selected_layer_id
        if current_id:
            self.video_service.unregister_source(current_id)
            self.timeline.remove_layer(current_id)
            self.state.remove_layer(current_id)
            self.sig_layer_removed.emit(current_id)
            self.select_layer(None)
            
            # Refresh dengan frame sekarang
            clean_time = self.frame_to_time(self.current_frame)
            self.seek_to(clean_time)
            self.sig_status_message.emit("🗑️ Layer Deleted")

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

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
        self.current_frame = 0 # Reset frame counter
        
        for l in layers:
            self._insert_layer(l)
            
        self.seek_to(0.0)
        self.sig_status_message.emit("✅ Project Loaded Successfully")

    def save_project(self, path=None):
        if not path: return
        if self.io_service.save_project(self.state, path):
            self.sig_status_message.emit(f"💾 Project Saved: {os.path.basename(path)}")
        else:
            self.sig_status_message.emit("❌ Save Failed")

    # =========================================================================
    # RENDER / EXPORT
    # =========================================================================
    
    def process_render(self, config):
        if self.timeline.get_total_duration() <= 0:
            self.sig_status_message.emit("❌ Timeline is empty!")
            return
            
        self.sig_status_message.emit("⏳ Preparing Render...")
        self.preview_engine.pause()
        
        # Inject Shared Video Service
        success, worker_or_msg = self.render_service.start_render_process(self.timeline, config, self.video_service)
        
        if success:
            worker = worker_or_msg
            worker.sig_progress.connect(self._on_render_progress)
            worker.sig_finished.connect(self._on_render_finished)
            worker.start()
        else:
            self.sig_status_message.emit(f"❌ {worker_or_msg}")

    def _on_render_progress(self, val):
        self.sig_status_message.emit(f"Rendering: {val}%")

    def _on_render_finished(self, success, result):
        msg = f"✅ Export Success: {result}" if success else f"❌ Export Failed: {result}"
        self.sig_status_message.emit(msg)

    # =========================================================================
    # HELPERS
    # =========================================================================
    
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
            
            # Live Update (Frame-based)
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

    # ... Service Proxies ...
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
        self.update_layer_property({
            "chroma_active": True, "chroma_color": color_hex, "chroma_threshold": threshold
        })

    def remove_chroma_config(self):
        self.update_layer_property({"chroma_active": False})
        
    def export_project(self): pass