import os
import json
from PySide6.QtWidgets import QInputDialog, QStyle, QFileDialog, QMessageBox
from PySide6.QtCore import Qt

from manager.media_manager import MediaManager
from gui.center_panel.video_item import VideoItem, BackgroundItem
from engine.caption.caption_flow import apply_caption
from gui.utils.bg_service import BackgroundService
from engine.render_engine import RenderWorker

class EditorController:
    def __init__(self, main_window):
        self.view = main_window
        self.preview = main_window.preview
        self.layer_panel = main_window.layer_panel
        self.setting = main_window.setting
        self.engine = main_window.engine
        
        self.bg_item = None
        self.audio_tracks = []
        self.worker = None
        
        self._connect_signals()

    def _connect_signals(self):
        # 1. Layer & Selection
        self.layer_panel.sig_layer_selected.connect(self.preview.select_frame_by_code)
        self.layer_panel.sig_layer_selected.connect(self.on_canvas_selection_update_ui)
        self.preview.sig_frame_selected.connect(self.layer_panel.select_layer_by_code)
        self.layer_panel.sig_layer_created.connect(self.on_create_visual_item)
        self.layer_panel.sig_layer_reordered.connect(self.on_layer_reordered)
        self.layer_panel.sig_delete_layer.connect(self.on_layer_deleted)

        # 2. Settings & Canvas Actions
        self.setting.on_setting_change.connect(self.on_setting_changed)
        self.preview.scene.selectionChanged.connect(self.on_canvas_selection_update_ui)
        self.preview.sig_item_moved.connect(self.on_canvas_item_moved)

        # 3. Media
        self.layer_panel.btn_add_bg.clicked.connect(self.on_add_bg_clicked)
        self.layer_panel.sig_bg_changed.connect(self.on_bg_properties_changed)
        self.layer_panel.sig_bg_toggle.connect(self.on_bg_toggle_changed)
        self.layer_panel.btn_add_content.clicked.connect(self.on_add_content_clicked)
        self.layer_panel.btn_add_text.clicked.connect(self.on_add_text_clicked)
        self.layer_panel.btn_add_paragraph.clicked.connect(self.on_add_paragraph_clicked)
        
        if hasattr(self.layer_panel, 'tab_audio'):
            self.layer_panel.tab_audio.music_list.btn_import.clicked.connect(self.on_import_audio_clicked)
            self.layer_panel.tab_audio.sfx_list.btn_import.clicked.connect(self.on_import_audio_clicked)
        self.layer_panel.btn_add_audio.clicked.connect(self.on_add_audio_clicked)

        if hasattr(self.layer_panel, 'tab_templates'):
            self.layer_panel.tab_templates.sig_load_template.connect(self.on_template_loaded)
        if hasattr(self.layer_panel, 'tab_chroma'):
            self.layer_panel.tab_chroma.btn_save_selection.clicked.connect(self.on_save_chroma_preset)
        
        self.preview.timeline_slider.valueChanged.connect(self.on_slider_moved)
        self.preview.btn_play.clicked.connect(self.engine.toggle_play)
        self.engine.sig_time_changed.connect(self.update_ui_from_engine)
        self.engine.sig_state_changed.connect(self.update_play_button_icon)
        
        self.setting.caption_tab.sig_generate_caption.connect(self.on_generate_caption)
        self.layer_panel.render_tab.btn_render.clicked.connect(self.on_render_clicked)
        self.layer_panel.render_tab.btn_stop.clicked.connect(self.on_stop_render_clicked)

    def on_setting_changed(self, data):
        selected = self.preview.scene.selectedItems()
        if not selected or not isinstance(selected[0], VideoItem): return
        item = selected[0]
        
        if data.get("type") == "text":
            item.settings.update(data)
            # Update ROTASI Teks
            if "rotation" in data:
                item.setRotation(data["rotation"])
            item.refresh_text_render()
        else:
            item.update_from_settings(data)
            item.settings.update({
                "x": int(item.pos().x()),
                "y": int(item.pos().y()),
                "scale": data["scale"],
                "rot": data["rotation"],
                "opacity": data["opacity"],
                "frame_rot": data["frame_rot"],
                "lock": data["lock"]
            })
        self.layer_panel.set_delete_enabled(not item.settings.get("lock"))

    def on_canvas_selection_update_ui(self):
        selected = self.preview.scene.selectedItems()
        is_video_item = False
        if selected and isinstance(selected[0], VideoItem):
            is_video_item = True
            item = selected[0]
            
            # SINKRONISASI NILAI DARI ITEM KE PANEL
            # Ambil nilai rotasi aktual dari item scene
            item.settings["rotation"] = int(item.rotation())
            
            self.setting.set_values(item.settings)
            content_type = item.settings.get("content_type", "media")
            
            # AUTO SWITCH TAB
            self.setting.set_active_tab_by_type(content_type)
            
            is_locked = item.settings.get("lock", False)
            self.layer_panel.set_delete_enabled(not is_locked)
            self.layer_panel.set_reorder_enabled(not is_locked)
        else:
            self.layer_panel.set_delete_enabled(False)
            self.layer_panel.set_reorder_enabled(False)
        if hasattr(self.layer_panel, 'set_content_button_enabled'):
            self.layer_panel.set_content_button_enabled(is_video_item)

    # --- TEXT & PARAGRAPH CREATION UPDATED ---
    def on_add_text_clicked(self): self._create_text_item("Judul", False)
    def on_add_paragraph_clicked(self): self._create_text_item("Paragraf...", True)
    
    def _create_text_item(self, default_text, is_paragraph):
        # Generate Nama untuk Layer
        count = self.layer_panel.list_layers.count()
        suffix = f"{'PARA' if is_paragraph else 'TXT'} {count}"
        full_name = f"FRAME {suffix}"
        
        # Tambah ke ListWidget Layer
        self.layer_panel.add_layer_item_custom(full_name)
        
        # Buat Item di Scene
        item = VideoItem(suffix, None, None, shape="text") 
        self.preview.scene.addItem(item)
        item.setPos(100, 100)
        item.set_text_content(default_text, is_paragraph=is_paragraph)
        
        self.preview.scene.clearSelection()
        item.setSelected(True)
        self.setting.set_values(item.settings)
        self.recalculate_global_duration()

    # --- RENDER LOGIC (UPDATED WITH BLUR & VIG) ---
    def on_render_clicked(self):
        output_path, _ = QFileDialog.getSaveFileName(self.view, "Simpan Video", "project_output.mp4", "Video Files (*.mp4)")
        if not output_path: return

        scene_rect = self.preview.scene.sceneRect()
        w_curr = scene_rect.width(); h_curr = scene_rect.height()
        if w_curr == h_curr: canvas_w, canvas_h = 1080, 1080
        elif w_curr < h_curr: canvas_w, canvas_h = 1080, 1920
        else: canvas_w, canvas_h = 1920, 1080
            
        if canvas_w != w_curr or canvas_h != h_curr: canvas_w, canvas_h = int(w_curr), int(h_curr)

        items_data = []
        scene_items = self.preview.scene.items()
        total_duration = self.engine.duration if self.engine.duration > 0 else 5.0
        valid_items = [i for i in scene_items if isinstance(i, VideoItem)]

        for item in valid_items:
            is_background = isinstance(item, BackgroundItem)
            is_text = item.settings.get("content_type") == "text"
            
            if not is_text and not item.file_path: continue

            if is_background:
                if item.current_pixmap: orig_w, orig_h = item.current_pixmap.width(), item.current_pixmap.height()
                else: orig_w, orig_h = canvas_w, canvas_h

                scale_factor = item.settings.get('scale', 100) / 100.0
                visual_w = int(orig_w * scale_factor)
                visual_h = int(orig_h * scale_factor)
                pos_x = item.settings.get('x', 0); pos_y = item.settings.get('y', 0)
                rot = 0; opacity = 100
            else:
                frame_rect = item.rect()
                visual_w = int(frame_rect.width()); visual_h = int(frame_rect.height())
                pos_x = int(item.x()); pos_y = int(item.y())
                rot = int(item.rotation()); opacity = item.settings.get('opacity', 100)

            if visual_w % 2 != 0: visual_w += 1
            if visual_h % 2 != 0: visual_h += 1

            item_data = {
                'path': item.file_path, 'is_bg': is_background, 'is_text': is_text,
                'text_pixmap': item.current_pixmap if is_text else None,
                'x': pos_x, 'y': pos_y, 'visual_w': visual_w, 'visual_h': visual_h,
                'rot': rot, 'opacity': opacity, 'z_value': item.zValue(),
                'start_time': 0, 'end_time': total_duration,
                # New Props
                'blur': item.settings.get('blur', 0),
                'vig': item.settings.get('vig', 0)
            }
            items_data.append(item_data)

        if not items_data: QMessageBox.warning(self.view, "Render", "Timeline kosong."); return

        self.layer_panel.render_tab.btn_render.setEnabled(False)
        self.layer_panel.render_tab.btn_render.setText("Rendering...")
        self.layer_panel.render_tab.btn_stop.setEnabled(True)
        
        self.worker = RenderWorker(items_data, output_path, total_duration, width=canvas_w, height=canvas_h, audio_tracks=self.audio_tracks)
        self.worker.sig_progress.connect(self.on_render_progress)
        self.worker.sig_finished.connect(self.on_render_finished)
        self.worker.start()

    def on_stop_render_clicked(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop(); self.layer_panel.render_tab.btn_stop.setText("Stopping...")

    def on_render_progress(self, msg): print(f"[RENDER] {msg}")
    def on_render_finished(self, success, msg):
        self.layer_panel.render_tab.btn_render.setEnabled(True); self.layer_panel.render_tab.btn_render.setText("🎬 MULAI RENDER")
        self.layer_panel.render_tab.btn_stop.setEnabled(False); self.layer_panel.render_tab.btn_stop.setText("🛑 STOP")
        if success: QMessageBox.information(self.view, "Sukses", msg)
        else: QMessageBox.warning(self.view, "Info", msg)

    # ... Helper Methods Lain (Recalculate, Create Visual Item, Add BG, dll) TETAP SAMA ...
    # Pastikan copy semua metode lama di sini.
    def recalculate_global_duration(self):
        max_duration = 0.0
        has_clips = False
        for item in self.preview.scene.items():
            if isinstance(item, VideoItem):
                if item.duration_s > max_duration: max_duration = item.duration_s
                has_clips = True
        if max_duration == 0 and not has_clips: max_duration = 5.0
        self.engine.set_duration(max_duration)
        self.preview.timeline_slider.setRange(0, int(max_duration * 100))

    def on_create_visual_item(self, frame_code, shape="portrait"):
        # [FIX] Tambahkan baris ini agar Frame Video/Image masuk ke daftar Layers
        full_name = f"FRAME {frame_code}"
        self.layer_panel.add_layer_item_custom(full_name)
        # -------------------------------------------------------------------

        item = VideoItem(frame_code, None, None, shape=shape)
        self.preview.scene.addItem(item)
        item.setPos(50, 50)
        item.settings.update({'x': 50, 'y': 50})
        self.preview.scene.clearSelection()
        item.setSelected(True)
        self.setting.set_values(item.settings)
        self.recalculate_global_duration()

    def on_add_bg_clicked(self):
        if not self.layer_panel.chk_bg_toggle.isChecked(): return
        data = MediaManager.open_media_dialog(self.view, "Pilih Background")
        if not data: return
        
        path = data['path']
        self.layer_panel.btn_add_bg.setText(f"BG: {data['name']}")
        self.engine.bg_layer.set_source(path)
        if self.bg_item: self.preview.scene.removeItem(self.bg_item)
        
        canvas_rect = self.preview.scene.sceneRect()
        self.bg_item = BackgroundItem(path, canvas_rect)
        self.bg_item.seek_to(0)
        
        geo_settings = BackgroundService.calculate_bg_geometry(self.bg_item.current_pixmap, canvas_rect)
        if geo_settings:
            self.bg_item.update_bg_settings(geo_settings)
            self.layer_panel.set_bg_values(self.bg_item.settings)
            self.layer_panel.show_bg_controls(True)
        
        self.preview.scene.addItem(self.bg_item)
        self.preview.scene.update()
        self.recalculate_global_duration()

    def on_bg_properties_changed(self, data):
        if self.bg_item: self.bg_item.update_bg_settings(data)
        if hasattr(self.engine, 'bg_layer'): self.engine.bg_layer.update_state(data)
        self.preview.scene.update()
    
    def on_bg_toggle_changed(self, is_on):
        if self.bg_item: self.bg_item.setVisible(is_on)
        self.engine.bg_layer.set_enabled(is_on)

    def on_add_content_clicked(self):
        selected = self.preview.scene.selectedItems()
        if not selected or not isinstance(selected[0], VideoItem): return
        target_item = selected[0]
        data = MediaManager.open_media_dialog(self.view)
        if not data: return
        target_item.set_content(data['path'])
        self.setting.set_values(target_item.settings)
        self.recalculate_global_duration()
        target_item.update()
        self.preview.scene.update()

    def on_import_audio_clicked(self):
        data = MediaManager.open_audio_dialog(self.view)
        if data:
            path = data['path']
            self.audio_tracks.append(path)
            QMessageBox.information(self.view, "Audio", f"Added: {data['name']}")
    def on_add_audio_clicked(self): self.on_import_audio_clicked()
    
    def on_template_loaded(self, template_data): pass
    def on_save_chroma_preset(self): pass
    
    def on_canvas_item_moved(self, settings_data): self.setting.set_values(settings_data)
    
    def on_layer_reordered(self):
        list_widget = self.layer_panel.list_layers
        count = list_widget.count()
        for i in range(count):
            item_list = list_widget.item(i)
            frame_name = item_list.text().replace("FRAME ", "")
            for graphics_item in self.preview.scene.items():
                if hasattr(graphics_item, 'name') and graphics_item.name == frame_name:
                    graphics_item.setZValue(count - i) 
                    break
        self.preview.scene.update()
        
    def on_layer_deleted(self, frame_code):
        scene = self.preview.scene
        for item in scene.items():
            if hasattr(item, 'name') and item.name == frame_code:
                scene.removeItem(item)
                break
        scene.update()
        self.recalculate_global_duration()

    def on_slider_moved(self, value):
        time_s = value / 100.0
        if not self.engine.timer.isActive(): self.engine.set_time(time_s)

    def update_ui_from_engine(self, t):
        self.preview.timeline_slider.blockSignals(True)
        self.preview.timeline_slider.setValue(int(t * 100))
        self.preview.timeline_slider.blockSignals(False)
        for item in self.preview.scene.items():
            if isinstance(item, VideoItem): item.seek_to(t)
            if self.bg_item: self.bg_item.seek_to(t)

    def update_play_button_icon(self, is_playing):
        icon = QStyle.SP_MediaPause if is_playing else QStyle.SP_MediaPlay
        self.preview.btn_play.setIcon(self.view.style().standardIcon(icon))

    def on_generate_caption(self, data):
        video_path = None
        for item in self.preview.scene.items():
            if isinstance(item, VideoItem):
                video_path = item.file_path
                break
        if not video_path: return
        base, ext = os.path.splitext(video_path)
        output = base + "_captioned.mp4"
        apply_caption(video_path=video_path, output_path=output, preset="karaoke")