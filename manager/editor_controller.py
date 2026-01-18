# manager/editor_controller.py

import json
import uuid
import os
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QUrl # <--- [FIX] Tambah QUrl
from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QDesktopServices
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
    sig_preview_update = Signal(float, list) 
    sig_render_started = Signal()          # Signal render mulai
    sig_render_finished = Signal(bool, str) # Signal render selesai (Success/Fail, Msg)
    sig_render_progress = Signal(int)       # Signal progress (0-100)

    def __init__(self):
        super().__init__()
        self.state = ProjectState()
        self.render_service = RenderService() # <--- INIT SERVICE
        
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
        
        # Connect Service Signals ke Controller Signals
        # (Asumsi RenderService punya signal: sig_progress, sig_finished, sig_error)
        if hasattr(self.render_service, 'sig_progress'):
            self.render_service.sig_progress.connect(self.sig_render_progress)
        
        if hasattr(self.render_service, 'sig_finished'):
            self.render_service.sig_finished.connect(self._on_service_render_finished)
            
        if hasattr(self.render_service, 'sig_error'):
            self.render_service.sig_error.connect(self._on_service_render_error)

        # Load Config
        self.config_file = "user_config.json"
        self.user_config = self._load_config()
        default_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.output_path = self.user_config.get("output_path", default_path)
        
    # --- RENDER LOGIC (IMPLEMENTASI BARU) ---

    def start_rendering_process(self, ui_config):
        """Dipanggil oleh UI saat tombol Export ditekan"""
        
        # 1. Tentukan Path Output (Folder)
        final_folder = ui_config.get('path')
        if not final_folder:
            final_folder = self.output_path # Default dari config/desktop
            
        # Validasi path folder
        if not os.path.isdir(final_folder):
            self.sig_status_message.emit("❌ Invalid Output Folder!")
            return

        # Ambil durasi total dari timeline
        total_duration = self.timeline.get_total_duration()

        # 2. Generate Nama File Unik (Timestamp)
        # Format: mamenpro_20260118_143005.mp4
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mamenpro_{timestamp}.mp4"
        
        # [PENTING] Gabungkan Folder + Filename jadi satu path lengkap
        full_output_path = os.path.join(final_folder, filename)

        # 3. Susun Konfigurasi
        render_config = {
            "output_path": full_output_path, # <--- [FIX] Service butuh key ini
            "quality": ui_config.get('quality', 'medium'),
            "width": self.state.width,
            "height": self.state.height,
            "fps": getattr(self, 'fps', 30),
            "layers": self.state.layers,
            "duration": total_duration if total_duration > 0 else 10 
        }

        # 4. Mulai Render
        self.sig_status_message.emit(f"🚀 Rendering to: {filename}...")
        self.sig_render_started.emit() 
        
        # Panggil Render Service
        success, worker_or_msg = self.render_service.start_render_process(
            self.timeline, render_config, self.video_service
        )

        if success:
            worker = worker_or_msg
            worker.sig_progress.connect(self.sig_render_progress)
            worker.sig_finished.connect(self._on_service_render_finished)
        else:
            self.sig_status_message.emit(f"❌ Failed to start: {worker_or_msg}")
            self.sig_render_finished.emit(False, worker_or_msg)
            
    def stop_rendering_process(self):
        """Dipanggil oleh UI saat tombol Stop ditekan"""
        self.render_service.cancel_render()
        self.sig_status_message.emit("🛑 Stopping Render...")
        
    # --- CONFIG MANAGEMENT ---
    def _load_config(self):
        """Load user_config.json, return dict kosong jika gagal"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        return {}

    def _save_config(self):
        """Simpan self.user_config ke file"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.user_config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    # --- OUTPUT FOLDER LOGIC ---
    def get_output_path(self):
        """Return current output path"""
        return self.output_path

    def select_output_directory(self, parent_widget=None):
        """Buka dialog pilih folder, simpan hasil, dan update config"""
        folder = QFileDialog.getExistingDirectory(
            parent_widget, 
            "Select Output Folder", 
            self.output_path
        )
        
        if folder:
            self.output_path = folder
            # Update config
            self.user_config["output_path"] = folder
            self._save_config()
            return True # Return true jika berubah
        return False

    def open_output_folder(self):
        """Buka folder output di Windows Explorer / Finder"""
        path_to_open = self.output_path
        
        # Pastikan path valid
        if path_to_open and os.path.isdir(path_to_open):
            # [FIX] Gunakan QDesktopServices yang sudah diimport
            url = QUrl.fromLocalFile(path_to_open)
            QDesktopServices.openUrl(url)
        else:
            self.sig_status_message.emit(f"⚠️ Folder not found: {path_to_open}")
            
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

    # --- CRUD LAYERS (CORE) ---
    def add_new_layer(self, layer_type, path=None, properties=None):
        """
        Generic Add Layer: Inserts at TOP (Track 0) and pushes others down.
        """
        # 1. Shift existing layers down
        for existing in self.state.layers:
            curr_track = existing.properties.get('track_index', 0)
            new_track = curr_track + 1
            existing.properties['track_index'] = new_track
            existing.z_index = 100 - new_track 
            
            self._sync_layer_to_timeline(existing)
            self.sig_property_changed.emit(existing.id, {
                "track_index": new_track,
                "z_index": existing.z_index
            })

        # 2. Create new layer data
        new_id = str(uuid.uuid4())[:8]
        name = f"{layer_type.upper()} {len(self.state.layers) + 1}"
        layer_data = LayerData(id=new_id, type=layer_type, name=name, path=path)
        
        # 3. Apply Default & Custom Properties
        layer_data.properties['track_index'] = 0
        layer_data.z_index = 100 
        
        if properties:
            layer_data.properties.update(properties)

        if layer_type == 'text' and 'text_content' not in layer_data.properties:
            layer_data.properties['text_content'] = "New Text"
            
        self._insert_layer(layer_data)

    # --- INTENT METHODS (SPECIFIC LOGIC) ---
    def add_text_layer(self, content="New Text", font_size=60):
        """Intent: Add Text with specific preset"""
        props = {
            "text_content": content,
            "font_size": font_size
        }
        self.add_new_layer("text", properties=props)
        self.sig_status_message.emit("📝 Text Added")

    def add_graphic_layer(self, path):
        """Intent: Add Overlay/Sticker"""
        self.add_new_layer("image", path=path)
        self.sig_status_message.emit("★ Graphic Added")

    def add_background_layer(self, path):
        """
        Intent: Add Background.
        Rule: Place at BOTTOM track (highest track index), Lowest Z-Index.
        Do NOT shift other layers.
        """
        if not path: return

        # 1. Determine Bottom Track Index
        current_max_track = 0
        if self.state.layers:
            current_max_track = max(l.properties.get('track_index', 0) for l in self.state.layers)
        
        new_track = current_max_track + 1
        
        # 2. Create Layer
        new_id = str(uuid.uuid4())[:8]
        name = f"BG {len(self.state.layers) + 1}"
        
        ext = os.path.splitext(path)[1].lower()
        l_type = "video" if ext in ['.mp4', '.mov', '.avi', '.mkv'] else "image"
        
        layer_data = LayerData(id=new_id, type=l_type, name=name, path=path)
        
        # 3. Apply Background Specifics
        layer_data.properties['track_index'] = new_track
        layer_data.z_index = -100 # Always behind
        
        # Logic Fit to Canvas could be added here if we had media info access
        # For now we rely on default or center logic
        
        # 4. Insert without shifting others
        if os.path.exists(layer_data.path):
            self.video_service.register_source(layer_data.id, layer_data.path)
        
        self.state.add_layer(layer_data)
        self._sync_layer_to_timeline(layer_data)
        
        self.sig_layer_created.emit(layer_data)
        self.sig_status_message.emit("🖼️ Background Added")


    def _insert_layer(self, layer_data: LayerData):
        if layer_data.type in ['video', 'image', 'audio'] and layer_data.path:
            if os.path.exists(layer_data.path):
                self.video_service.register_source(layer_data.id, layer_data.path)
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

    def move_layer_time(self, layer_id: str, new_start_time: float, track_index: int = -1):
        if new_start_time < 0: new_start_time = 0.0
        frame_start = self.time_to_frame(new_start_time)
        clean_start_time = self.frame_to_time(frame_start)
        
        self.state.selected_layer_id = layer_id
        props = {"start_time": clean_start_time}
        if track_index >= 0:
            props["track_index"] = track_index

        self.update_layer_property(layer_id, props)
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

    def select_layer(self, layer_id):
        self.state.selected_layer_id = layer_id
        layer = self.state.get_layer(layer_id)
        self.sig_selection_changed.emit(layer)

    def update_layer_property(self, arg1, arg2=None, arg3=None):
        layer_id = None
        new_props = {}

        if isinstance(arg1, dict):
            layer_id = self.state.selected_layer_id
            new_props = arg1
        elif isinstance(arg1, str) and isinstance(arg2, dict):
            layer_id = arg1
            new_props = arg2
        elif isinstance(arg1, str) and isinstance(arg2, str):
            layer_id = arg1
            new_props = {arg2: arg3}
        else:
            return

        if not layer_id: return
        layer = self.state.get_layer(layer_id)
        if layer:
            layer.properties.update(new_props)
            if any(k in new_props for k in ["start_time", "duration", "track_index"]):
                self._sync_layer_to_timeline(layer)
            
            self.sig_property_changed.emit(layer_id, new_props)
            clean_time = self.frame_to_time(self.current_frame)
            self.seek_to(clean_time)

    def reorder_layers(self, from_idx: int, to_idx: int):
        if from_idx < 0 or to_idx < 0: return
        if from_idx >= len(self.state.layers) or to_idx >= len(self.state.layers): return
        layer = self.state.layers.pop(from_idx)
        self.state.layers.insert(to_idx, layer)
        self.select_layer(layer.id)

    def update_canvas_resolution(self, width: int, height: int):
        self.state.width = width
        self.state.height = height
        self.sig_status_message.emit(f"📐 Resolution set to {width}x{height}")

    # --- RENDER ---
    def process_render(self, config):
        if self.timeline.get_total_duration() <= 0:
            self.sig_status_message.emit("❌ Timeline is empty!")
            return
            
        self.sig_status_message.emit("⏳ Preparing Render...")
        self.preview_engine.pause()
        
        # Inject Resolusi
        render_config = config.copy()
        render_config["width"] = self.state.width
        render_config["height"] = self.state.height
        
        # [FIX] Kirim 3 Parameter: timeline, settings, video_service
        success, worker_or_msg = self.render_service.start_render_process(
            self.timeline, render_config, self.video_service
        )
        
        if success:
            worker = worker_or_msg
            worker.sig_progress.connect(self._on_render_progress)
            worker.sig_finished.connect(self._on_render_finished)
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
        for l in layers: 
            if 'track_index' not in l.properties:
                l.properties['track_index'] = 0
            l.z_index = 100 - l.properties['track_index']
            self._insert_layer(l)
            
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
        for i, l in enumerate(layers):
            l.properties['track_index'] = i
            l.z_index = 100 - i
            self._insert_layer(l)

    def add_audio_layer(self, path):
        new_id = str(uuid.uuid4())[:8]
        name = f"AUDIO {len(self.state.layers) + 1}"
        layer = LayerData(id=new_id, type="audio", name=name, path=path)
        layer.properties['track_index'] = 5 
        layer.z_index = 95
        self._insert_layer(layer)

    def generate_auto_captions(self, config):
        # Intent: Generate Caption
        # This calls the service, which will eventually return layers via signal
        current = self.state.get_layer(self.state.selected_layer_id)
        if current and current.path:
            self.sig_status_message.emit("🎙️ Generating Captions...")
            self.cap_service.start_generate_async(current.path, config)
        else:
            self.sig_status_message.emit("⚠️ Select video layer first.")
    
    def process_bulk_render(self, bulk_data):
        # Intent: Process Bulk (Placeholder logic for now)
        # This would typically loop through data and create layers or render jobs
        count = len(bulk_data.get("raw_data", []))
        self.sig_status_message.emit(f"🚀 Bulk Process Started: {count} items")

    def _on_caption_success(self, layer_models: list):
        for model in layer_models:
            layer_data = LayerData(
                id=model.id, type="text", name="Subtitle", path=None, properties=model.payload
            )
            layer_data.properties["start_time"] = model.time.start
            layer_data.properties["duration"] = model.time.duration
            layer_data.properties["track_index"] = 0
            layer_data.z_index = 100
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
    # --- INTERNAL HANDLERS ---

    def _on_service_render_finished(self, output_file):
        self.sig_render_finished.emit(True, f"Saved to: {output_file}")
        self.sig_status_message.emit(f"✅ Render Success: {output_file}")

    def _on_service_render_error(self, error_msg):
        self.sig_render_finished.emit(False, error_msg)
        self.sig_status_message.emit(f"❌ Render Failed: {error_msg}")