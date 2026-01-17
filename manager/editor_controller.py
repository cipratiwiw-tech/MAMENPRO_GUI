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
        
        # 1. CORE VIDEO SERVICE (Shared Instance)
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

    # =========================================================================
    # CORE LOOP & PREVIEW
    # =========================================================================
    def _on_engine_tick(self, t: float):
        # 1. Ambil Layer ID yang aktif di detik ke-t dari Timeline Engine
        active_models = self.timeline.get_active_layers(t)
        active_ids = [l.id for l in active_models]
        
        # 2. Kirim ke Binder -> UI
        # UI akan menggunakan ID ini untuk minta frame ke VideoService
        self.sig_preview_update.emit(t, active_ids)

    def _on_playback_state(self, is_playing: bool):
        state = "▶️ PLAYING" if is_playing else "⏸️ PAUSED"
        self.sig_status_message.emit(state)

    def toggle_play(self):
        # Pastikan durasi preview engine update sesuai timeline
        total_dur = self.timeline.get_total_duration()
        self.preview_engine.set_duration(max(total_dur + 1.0, 5.0))
        self.preview_engine.toggle_play()
        
    def seek_to(self, t: float):
        # Force update preview ke waktu t
        self.preview_engine.seek(t)
        # Manual trigger tick agar UI langsung update saat scrubbing/seek
        self._on_engine_tick(self.preview_engine.current_time)

    # =========================================================================
    # CRUD LAYERS (CORE FLOW LOGIC)
    # =========================================================================

    def add_new_layer(self, layer_type, path=None):
        """Entry point dari UI untuk menambah layer baru"""
        new_id = str(uuid.uuid4())[:8]
        name = f"{layer_type.upper()} {len(self.state.layers) + 1}"
        
        # Buat Data Murni
        layer_data = LayerData(id=new_id, type=layer_type, name=name, path=path)
        
        # Default properties agar tidak 'zonk'
        if layer_type == 'text':
            layer_data.properties['text_content'] = "New Text"
        
        self._insert_layer(layer_data)

    def _insert_layer(self, layer_data: LayerData):
        """Internal logic untuk memasukkan layer ke sistem"""
        # 1. Register Source ke VideoService (PENTING AGAR TIDAK BLANK)
        if layer_data.type in ['video', 'image', 'audio'] and layer_data.path:
            if os.path.exists(layer_data.path):
                self.video_service.register_source(layer_data.id, layer_data.path)
            else:
                self.sig_status_message.emit(f"⚠️ File not found: {layer_data.path}")

        # 2. Update State
        self.state.add_layer(layer_data)
        
        # 3. Update Timeline Engine
        self._sync_layer_to_timeline(layer_data)
        
        # 4. Notify UI
        self.sig_layer_created.emit(layer_data)
        self.select_layer(layer_data.id)
        
        # 5. FORCE UPDATE PREVIEW (Anti-Zonk)
        # Langsung seek ke start_time layer agar user melihat hasilnya
        start_t = float(layer_data.properties.get("start_time", 0.0))
        self.seek_to(start_t)
        
        self.sig_status_message.emit(f"✅ Layer Added: {layer_data.name}")

    def _sync_layer_to_timeline(self, layer_data: LayerData):
        """Konversi Data -> Model Timeline"""
        self.timeline.remove_layer(layer_data.id)
        
        start = float(layer_data.properties.get("start_time", 0.0))
        duration = float(layer_data.properties.get("duration", 5.0))
        
        model = LayerModel(
            id=layer_data.id,
            type=layer_data.type,
            time=TimeRange(start, start + duration),
            z_index=layer_data.z_index,
            payload=layer_data.properties  # Kirim semua properties ke payload
        )
        # Payload khusus untuk path (penting buat render engine)
        if layer_data.path:
            model.payload["path"] = layer_data.path

        self.timeline.add_layer(model)
        
        # Update durasi preview engine
        total_dur = self.timeline.get_total_duration()
        self.preview_engine.set_duration(max(total_dur + 1.0, 5.0))

    def move_layer_time(self, layer_id: str, new_start_time: float):
        if new_start_time < 0: new_start_time = 0.0
        
        # Update property
        self.state.selected_layer_id = layer_id
        props = {"start_time": new_start_time}
        self.update_layer_property(props)
        
        # Feedback visual instant
        self.seek_to(new_start_time)

    def delete_current_layer(self):
        current_id = self.state.selected_layer_id
        if current_id:
            # 1. Cleanup Service
            self.video_service.unregister_source(current_id)

            # 2. Cleanup Engines
            self.timeline.remove_layer(current_id)
            self.state.remove_layer(current_id)
            
            # 3. Notify UI
            self.sig_layer_removed.emit(current_id)
            self.select_layer(None)
            
            # 4. Refresh Preview
            self._on_engine_tick(self.preview_engine.current_time)
            self.sig_status_message.emit("🗑️ Layer Deleted")

    # =========================================================================
    # STATE MANAGEMENT (SAVE/LOAD)
    # =========================================================================

    def load_project(self, path):
        self.sig_status_message.emit("📂 Loading Project...")
        
        # 1. Load Data Murni
        layers = self.io_service.load_project(path)
        if layers is None:
            self.sig_status_message.emit("❌ Failed to load project")
            return

        # 2. Reset Total System
        self.preview_engine.pause()
        self.state.layers.clear()
        self.timeline.clear()
        self.video_service.release_all() # Reset cache video
        self.sig_layer_cleared.emit() # Bersihkan UI
        
        # 3. Reconstruct
        for l in layers:
            # Kita panggil internal insert agar ID dari file tetap terjaga
            # JANGAN panggil add_new_layer karena itu bikin ID baru
            self._insert_layer(l)
            
        # 4. Reset View
        self.seek_to(0.0)
        self.sig_status_message.emit("✅ Project Loaded Successfully")

    def save_project(self, path=None):
        if not path:
            self.sig_status_message.emit("⚠️ Save path invalid")
            return
        if self.io_service.save_project(self.state, path):
            self.sig_status_message.emit(f"💾 Project Saved: {os.path.basename(path)}")
        else:
            self.sig_status_message.emit("❌ Save Failed")

    # =========================================================================
    # RENDER / EXPORT
    # =========================================================================
    
    def process_render(self, config):
        if self.timeline.get_total_duration() <= 0:
            self.sig_status_message.emit("❌ Timeline is empty! Cannot render.")
            return
            
        self.sig_status_message.emit("⏳ Preparing Render...")
        self.preview_engine.pause() # Stop preview biar gak rebutan resource
        
        success, worker_or_msg = self.render_service.start_render_process(self.timeline, config)
        
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
        if success:
            self.sig_status_message.emit(f"✅ Export Success: {result}")
        else:
            self.sig_status_message.emit(f"❌ Export Failed: {result}")

    # =========================================================================
    # HELPERS & OTHERS
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
            
            # Jika properti waktu berubah, wajib sync timeline
            if "start_time" in new_props or "duration" in new_props:
                self._sync_layer_to_timeline(layer)
            
            self.sig_property_changed.emit(current_id, new_props)
            # Update visual langsung
            self._on_engine_tick(self.preview_engine.current_time)
            
    def reorder_layers(self, from_idx: int, to_idx: int):
        # ... (Logika reorder tetap sama, pastikan _sync_layer_to_timeline dipanggil) ...
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
        self._on_engine_tick(self.preview_engine.current_time)

    # ... (Service Proxies: apply_template, caption, chroma, dll TETAP SAMA) ...
    def apply_template(self, tpl_id):
        layers = self.tpl_service.generate_layers(tpl_id)
        for l in layers:
            self._insert_layer(l)

    def add_audio_layer(self, path):
        self.add_new_layer("audio", path)

    def generate_auto_captions(self, config):
        current = self.state.get_layer(self.state.selected_layer_id)
        if current and current.path:
            self.sig_status_message.emit("🎙️ Generating Captions...")
            self.cap_service.start_generate_async(current.path, config)
        else:
            self.sig_status_message.emit("⚠️ Select a video/audio layer first.")

    def _on_caption_success(self, layer_models: list):
        for model in layer_models:
            # Konversi Model -> LayerData
            layer_data = LayerData(
                id=model.id,
                type="text",
                name="Subtitle",
                path=None,
                properties=model.payload
            )
            # Properties waktu perlu diekstrak dari TimeRange
            layer_data.properties["start_time"] = model.time.start
            layer_data.properties["duration"] = model.time.duration
            
            self._insert_layer(layer_data)
        self.sig_status_message.emit(f"✅ Generated {len(layer_models)} captions")

    def _on_caption_error(self, msg):
        self.sig_status_message.emit(f"❌ Caption Error: {msg}")

    def apply_chroma_config(self, color_hex: str, threshold: float):
        self.update_layer_property({
            "chroma_active": True,
            "chroma_color": color_hex,
            "chroma_threshold": threshold
        })

    def remove_chroma_config(self):
        self.update_layer_property({"chroma_active": False})
    
    # [NEW] Export Project method for Binder mapping
    def export_project(self):
        # Trigger default render config (bisa dikembangkan)
        pass