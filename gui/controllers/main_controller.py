import os
from PySide6.QtWidgets import QStyle, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, QTimer

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
        # Validasi awal (Tombol render mati jika kosong)
        self.validate_render_state()

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

        # 3. Media & Content
        self.layer_panel.btn_add_bg.clicked.connect(self.on_add_bg_clicked)
        self.layer_panel.sig_bg_changed.connect(self.on_bg_properties_changed)
        self.layer_panel.sig_bg_toggle.connect(self.on_bg_toggle_changed)
        self.layer_panel.btn_add_content.clicked.connect(self.on_add_content_clicked)
        self.layer_panel.btn_add_text.clicked.connect(self.on_add_text_clicked)
        self.layer_panel.btn_add_paragraph.clicked.connect(self.on_add_paragraph_clicked)
        
        # 4. Audio
        if hasattr(self.layer_panel, 'tab_audio'):
            self.layer_panel.tab_audio.music_list.btn_import.clicked.connect(self.on_import_audio_clicked)
            self.layer_panel.tab_audio.sfx_list.btn_import.clicked.connect(self.on_import_audio_clicked)
        self.layer_panel.btn_add_audio.clicked.connect(self.on_add_audio_clicked)

        # 5. Templates & Engine
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
        
        self.preview.sig_item_moved.connect(self.on_visual_item_moved)
        self.layer_panel.sig_layer_created.connect(self.validate_render_state)
        self.layer_panel.sig_delete_layer.connect(self.validate_render_state)
        self.layer_panel.sig_bg_toggle.connect(self.validate_render_state)
        self.layer_panel.sig_bg_changed.connect(self.validate_render_state) 
        self.layer_panel.btn_add_bg.clicked.connect(lambda: QTimer.singleShot(500, self.validate_render_state))
        
        if hasattr(self.preview.view, 'sig_dropped'):
            self.preview.view.sig_dropped.connect(self.validate_render_state)
            
    def validate_render_state(self, *args):
        """Tombol Render AKTIF jika ada BG atau Clip di scene."""
        has_bg = self.layer_panel.chk_bg_toggle.isChecked() and (self.bg_item is not None)
        has_clips = any(isinstance(item, VideoItem) and not isinstance(item, BackgroundItem) 
                       for item in self.preview.scene.items())
        
        can_render = has_bg or has_clips
        btn = self.layer_panel.render_tab.btn_render
        btn.setEnabled(can_render)
        
        if can_render:
            btn.setStyleSheet("background-color: #2a9d8f; color: white; font-size: 14px; font-weight: bold;")
            btn.setToolTip("Siap Render")
        else:
            btn.setStyleSheet("background-color: #555555; color: #aaaaaa; font-size: 14px; font-weight: bold;")
            btn.setToolTip("Scene kosong! Tambahkan BG atau Clip.")
            
    def on_visual_item_moved(self, data):
        self.setting.set_values(data)
        if data.get("is_bg", False):
            self.layer_panel.set_bg_values(data)
                
    def recalculate_global_duration(self):
        """Scan semua layer, cari end_time terpanjang, dan set sebagai durasi global."""
        max_end = 5.0
        for item in self.preview.scene.items():
            if isinstance(item, VideoItem):
                end_t = getattr(item, 'end_time', None)
                if end_t is not None and end_t > max_end:
                    max_end = end_t
        
        self.engine.set_duration(max_end)
        self.preview.timeline_slider.blockSignals(True)
        self.preview.timeline_slider.setRange(0, int(max_end * 100))
        self.preview.timeline_slider.blockSignals(False)
        print(f"[AUTO-DURATION] Global Duration Updated to: {max_end:.2f}s")
        
    def on_setting_changed(self, data):
        selected = self.preview.scene.selectedItems()
        if not selected or not isinstance(selected[0], VideoItem): return
        item = selected[0]
        
        if "start_time" in data or "end_time" in data:
            new_start = float(data.get("start_time", item.start_time))
            new_end = float(data.get("end_time", item.end_time if item.end_time is not None else new_start + 5.0))
            new_dur = max(0.1, new_end - new_start)
            item.set_time_range(new_start, new_dur)
            self.recalculate_global_duration()
            item.apply_global_time(self.engine.current_time)
        
        filtered_data = {k: v for k, v in data.items() if k not in ['start_time', 'end_time']}
        item.settings.update(filtered_data)

        if data.get("type") == "text":
            if "rotation" in data: item.setRotation(data["rotation"])
            item.refresh_text_render()
        else:
            if "x" in data and "y" in data: item.setPos(data["x"], data["y"])
            if "frame_rot" in data: item.setRotation(data["frame_rot"])
            if "frame_w" in data and "frame_h" in data:
                item.setRect(0, 0, data["frame_w"], data["frame_h"])
                item.setTransformOriginPoint(item.rect().center())
            item.update() 
        self.layer_panel.set_delete_enabled(not item.settings.get("lock"))

    def on_canvas_selection_update_ui(self):
        selected = self.preview.scene.selectedItems()
        enable_content_buttons = False
        
        if selected and isinstance(selected[0], VideoItem):
            item = selected[0]
            is_bg = isinstance(item, BackgroundItem)
            enable_content_buttons = not is_bg
            
            item.settings.update({
                "x": int(item.pos().x()),
                "y": int(item.pos().y()),
                "frame_rot": int(item.rotation()),
                "frame_w": int(item.rect().width()),
                "frame_h": int(item.rect().height()),
                "start_time": item.start_time,
                "end_time": item.end_time
            })
            
            self.setting.set_values(item.settings)
            self.setting.set_active_tab_by_type(item.settings.get("content_type", "media"))
            is_locked = item.settings.get("lock", False)
            self.layer_panel.set_delete_enabled(not is_locked and not is_bg)
            self.layer_panel.set_reorder_enabled(not is_locked and not is_bg)
        else:
            self.layer_panel.set_delete_enabled(False)
            self.layer_panel.set_reorder_enabled(False)
            
        if hasattr(self.layer_panel, 'set_content_button_enabled'):
            self.layer_panel.set_content_button_enabled(enable_content_buttons)

    def on_create_visual_item(self, frame_code, shape="portrait"):
        self.layer_panel.add_layer_item_custom(f"FRAME {frame_code}")
        item = VideoItem(frame_code, None, None, shape=shape)
        self.preview.scene.addItem(item)
        item.setPos(50, 50)
        item.settings.update({'x': 50, 'y': 50})
        self.preview.scene.clearSelection()
        item.setSelected(True)
        self.recalculate_global_duration()
        self.validate_render_state()

    def on_add_text_clicked(self): self._create_text_item("Judul", False)
    def on_add_paragraph_clicked(self): self._create_text_item("Paragraf...", True)
    
    def _create_text_item(self, default_text, is_paragraph):
        count = self.layer_panel.list_layers.count()
        suffix = f"{'PARA' if is_paragraph else 'TXT'} {count}"
        self.layer_panel.add_layer_item_custom(f"FRAME {suffix}")
        item = VideoItem(suffix, None, None, shape="text") 
        self.preview.scene.addItem(item)
        item.setPos(100, 100)
        item.set_text_content(default_text, is_paragraph=is_paragraph)
        self.preview.scene.clearSelection()
        item.setSelected(True)
        self.setting.set_values(item.settings)
        self.recalculate_global_duration()

    # ... (bagian lain kode tetap sama) ...

    def on_render_clicked(self):
        # 1. Recalculate Durasi Global & Validasi
        self.recalculate_global_duration()
        current_duration = self.engine.duration
        
        if current_duration <= 0.1:
            QMessageBox.warning(self.view, "Render Gagal", "Timeline kosong atau durasi 0 detik.")
            return

        # 2. Get Canvas Size
        scene_rect = self.preview.scene.sceneRect()
        w_curr = int(scene_rect.width())
        h_curr = int(scene_rect.height())

        # 3. Path Dialog
        output_path, _ = QFileDialog.getSaveFileName(self.view, "Simpan Video", "output.mp4", "Video Files (*.mp4)")
        if not output_path: return

        # 4. Logic Resolusi
        if w_curr == h_curr: canvas_w, canvas_h = 1080, 1080
        elif w_curr < h_curr: canvas_w, canvas_h = 1080, 1920
        else: canvas_w, canvas_h = 1920, 1080
        
        # 5. Collect Data
        items_data = []
        sw, sh = float(w_curr), float(h_curr)
        
        # Hanya ambil item VideoItem yang aktif
        active_items = [i for i in self.preview.scene.items() if isinstance(i, VideoItem)]

        for item in active_items:
            # 🛡️ SAFETY: Pastikan item punya atribut waktu
            start_t = float(getattr(item, 'start_time', 0.0) or 0.0)
            end_t = float(getattr(item, 'end_time', current_duration) or current_duration)
            
            # Skip jika durasi tayang item 0 (tidak terlihat)
            if end_t <= start_t: continue

            is_bg = isinstance(item, BackgroundItem)
            is_text = item.settings.get("content_type") == "text"
            
            if is_bg:
                if not self.layer_panel.chk_bg_toggle.isChecked(): continue
                if not item.current_pixmap: continue
                
                scale = item.settings.get('scale', 100) / 100.0
                vw = int(item.current_pixmap.width() * scale)
                vh = int(item.current_pixmap.height() * scale)
                
                px = int((sw/2 + item.settings.get('x', 0)) - (vw/2))
                py = int((sh/2 + item.settings.get('y', 0)) - (vh/2))
            else:
                # 🛡️ SAFETY: Pastikan integer
                vw, vh = int(item.rect().width()), int(item.rect().height())
                px, py = int(item.x()), int(item.y())

            # Skip item yang ukurannya 0 (bikin FFmpeg error scale)
            if vw <= 0 or vh <= 0: continue

            items_data.append({
                'path': item.file_path, 
                'is_bg': is_bg, 
                'is_text': is_text,
                'text_pixmap': item.current_pixmap if is_text else None,
                'x': px, 'y': py, 
                'visual_w': vw, 'visual_h': vh,
                'rot': int(item.rotation()),
                'opacity': item.settings.get('opacity', 100),
                'z_value': item.zValue(),
                'blur': item.settings.get('blur', 0),
                'vig': item.settings.get('vig', 0),
                'start_time': start_t,
                'end_time': end_t
            })

        if not items_data:
            QMessageBox.warning(self.view, "Render Gagal", "Tidak ada layer aktif yang bisa dirender.")
            return

        # 6. Execute Render
        self.layer_panel.render_tab.btn_render.setEnabled(False)
        self.layer_panel.render_tab.btn_render.setText("Rendering...")
        
        self.worker = RenderWorker(items_data, output_path, current_duration, canvas_w, canvas_h, self.audio_tracks)
        self.worker.sig_progress.connect(self.on_render_progress)
        self.worker.sig_finished.connect(self.on_render_finished)
        self.worker.start()

    # ... (sisa kode controller tetap sama) ...


    @staticmethod
    def validate_before_render(items_data, total_duration):
        if not items_data:
            return False, (
                "Tidak ada layer yang bisa dirender.\n\n"
                "Pastikan:\n"
                "- Background aktif atau\n"
                "- Clip memiliki durasi yang cukup."
            )

        if total_duration <= 0.1:
            return False, "Durasi proyek tidak valid."

        # ✅ LOGIKA BENAR: ada layer yang benar-benar terlihat
        has_visible_layer = any(
            it['end_time'] > it['start_time']
            for it in items_data
        )

        if not has_visible_layer:
            return False, (
                "Layer terlalu singkat atau tidak terlihat.\n"
                "Perpanjang durasi layer di timeline."
            )

        return True, None


    def on_stop_render_clicked(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.layer_panel.render_tab.btn_stop.setText("Stopping...")

    def on_render_progress(self, msg): print(f"[RENDER] {msg}")
    
    def on_render_finished(self, success, msg):
        self.layer_panel.render_tab.btn_render.setEnabled(True)
        self.layer_panel.render_tab.btn_render.setText("🎬 MULAI RENDER")
        self.layer_panel.render_tab.btn_stop.setEnabled(False)
        if success: QMessageBox.information(self.view, "Sukses", msg)
        else: QMessageBox.warning(self.view, "Info", msg)

    def on_add_bg_clicked(self):
        if not self.layer_panel.chk_bg_toggle.isChecked(): return
        data = MediaManager.open_media_dialog(self.view, "Pilih Background")
        if not data: return
        if self.bg_item: self.preview.scene.removeItem(self.bg_item)
        
        self.bg_item = BackgroundItem(data['path'], self.preview.scene.sceneRect())
        self.bg_item.seek_to(0)
        self.bg_item.update_bg_settings({'x': 0, 'y': 0, 'scale': 100, 'fit': 'cover', 'blur': 0, 'vig': 0})
        
        self.layer_panel.set_bg_values(self.bg_item.settings)
        self.layer_panel.show_bg_controls(True)
        self.preview.scene.addItem(self.bg_item)
        self.recalculate_global_duration()
        self.validate_render_state()

    def on_add_content_clicked(self):
        selected = self.preview.scene.selectedItems()
        if not selected or not isinstance(selected[0], VideoItem): return
        data = MediaManager.open_media_dialog(self.view)
        if data:
            selected[0].set_content(data['path'])
            self.setting.set_values(selected[0].settings)
            self.recalculate_global_duration()
            self.preview.scene.update()
            
    def on_layer_reordered(self):
        lw = self.layer_panel.list_layers
        for i in range(lw.count()):
            name = lw.item(i).text().replace("FRAME ", "")
            for g_item in self.preview.scene.items():
                if hasattr(g_item, 'name') and g_item.name == name:
                    g_item.setZValue(lw.count() - i)
                    break
        self.preview.scene.update()

    def on_layer_deleted(self, frame_code):
        for item in self.preview.scene.items():
            if hasattr(item, 'name') and item.name == frame_code:
                self.preview.scene.removeItem(item)
                break
        self.recalculate_global_duration()
        self.validate_render_state()

    def update_ui_from_engine(self, t):
        self.preview.timeline_slider.blockSignals(True)
        self.preview.timeline_slider.setValue(int(t * 100))
        self.preview.timeline_slider.blockSignals(False)
        for item in self.preview.scene.items():
            if hasattr(item, 'apply_global_time'): item.apply_global_time(t)
            elif hasattr(item, 'seek_to'): item.seek_to(t)

    def on_slider_moved(self, value):
        if not self.engine.timer.isActive():
            self.engine.set_time(value / 100.0)

    def update_play_button_icon(self, is_playing):
        icon = QStyle.SP_MediaPause if is_playing else QStyle.SP_MediaPlay
        self.preview.btn_play.setIcon(self.view.style().standardIcon(icon))

    def on_generate_caption(self, data):
        for item in self.preview.scene.items():
            if isinstance(item, VideoItem) and item.file_path:
                output = os.path.splitext(item.file_path)[0] + "_captioned.mp4"
                apply_caption(video_path=item.file_path, output_path=output, preset="karaoke")
                break

    def on_bg_properties_changed(self, data):
        if self.bg_item: self.bg_item.update_bg_settings(data)
    def on_bg_toggle_changed(self, is_on):
        if self.bg_item: self.bg_item.setVisible(is_on)
    def on_import_audio_clicked(self):
        data = MediaManager.open_audio_dialog(self.view)
        if data: self.audio_tracks.append(data['path'])
    def on_add_audio_clicked(self): self.on_import_audio_clicked()
    def on_canvas_item_moved(self, data): self.setting.set_values(data)
    def on_template_loaded(self, data): pass
    def on_save_chroma_preset(self): pass