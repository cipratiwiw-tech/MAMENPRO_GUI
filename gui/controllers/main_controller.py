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
        self.audio_tracks = []  # List untuk menyimpan path audio tambahan
        
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

        # 3. Left Panel Action Buttons (Media/Content)
        self.layer_panel.btn_add_bg.clicked.connect(self.on_add_bg_clicked)
        self.layer_panel.sig_bg_changed.connect(self.on_bg_properties_changed)
        self.layer_panel.sig_bg_toggle.connect(self.on_bg_toggle_changed)
        
        self.layer_panel.btn_add_content.clicked.connect(self.on_add_content_clicked)
        self.layer_panel.btn_add_text.clicked.connect(self.on_add_text_clicked)
        self.layer_panel.btn_add_paragraph.clicked.connect(self.on_add_paragraph_clicked)
        
        # --- AUDIO FEATURES ---
        # Audio Tab di Left Panel (Import buttons)
        if hasattr(self.layer_panel, 'tab_audio'):
            self.layer_panel.tab_audio.music_list.btn_import.clicked.connect(self.on_import_audio_clicked)
            self.layer_panel.tab_audio.sfx_list.btn_import.clicked.connect(self.on_import_audio_clicked)
        # Tombol Add Audio di panel editor (atas)
        self.layer_panel.btn_add_audio.clicked.connect(self.on_add_audio_clicked)

        # --- TEMPLATE & PRESET FEATURES ---
        if hasattr(self.layer_panel, 'tab_templates'):
            self.layer_panel.tab_templates.sig_load_template.connect(self.on_template_loaded)
        if hasattr(self.layer_panel, 'tab_chroma'):
            self.layer_panel.tab_chroma.btn_save_selection.clicked.connect(self.on_save_chroma_preset)
        
        # 4. Engine & Timeline
        self.preview.timeline_slider.valueChanged.connect(self.on_slider_moved)
        self.preview.btn_play.clicked.connect(self.engine.toggle_play)
        self.engine.sig_time_changed.connect(self.update_ui_from_engine)
        self.engine.sig_state_changed.connect(self.update_play_button_icon)
        
        # 5. Caption & Render
        self.setting.caption_tab.sig_generate_caption.connect(self.on_generate_caption)
        self.layer_panel.render_tab.btn_render.clicked.connect(self.on_render_clicked)
    def on_add_text_clicked(self):
        self._create_text_item("Judul", is_paragraph=False)

    def on_add_paragraph_clicked(self):
        self._create_text_item("Paragraf Baru\nKetik disini...", is_paragraph=True)

    def _create_text_item(self, default_text, is_paragraph):
        frame_code = f"TXT_{len(self.preview.scene.items())}"
        # Shape "text" akan mentrigger ukuran default di VideoItem
        item = VideoItem(frame_code, None, None, shape="text") 
        self.preview.scene.addItem(item)
        
        item.setPos(100, 100)
        item.set_text_content(default_text, is_paragraph=is_paragraph)
        
        self.preview.scene.clearSelection()
        item.setSelected(True)
        self.setting.set_values(item.settings)
        self.recalculate_global_duration()
        print(f"[CTRL] Created Text Item (Para={is_paragraph})")
    # ==========================
    # LOGIC UTAMA (Handler)
    # ==========================

    def on_setting_changed(self, data):
        selected = self.preview.scene.selectedItems()
        if not selected or not isinstance(selected[0], VideoItem): return
        
        item = selected[0]
        
        if data.get("type") == "text":
            # Update atribut teks
            item.settings.update(data)
            # Render ulang visual teks
            item.refresh_text_render()
            
            # Jika user ngetik panjang, box mungkin perlu resize otomatis?
            # Di VideoItem refresh_text_render, kita tidak ubah rect kecuali mode auto-fit.
            # Tapi karena kita sekarang punya HANDLE RESIZE manual, biarkan user yang atur ukuran box.
        else:
            # Update transformasi biasa (posisi, rotasi, dll)
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

    # --- AUDIO HANDLERS ---
    def on_import_audio_clicked(self):
        """Handler untuk tombol import di Audio Tab"""
        data = MediaManager.open_audio_dialog(self.view)
        if data:
            path = data['path']
            self.audio_tracks.append(path)
            print(f"[AUDIO] Added to track: {path}")
            QMessageBox.information(self.view, "Audio", f"Audio berhasil ditambahkan ke antrian render:\n{data['name']}")

    def on_add_audio_clicked(self):
        """Handler tombol Add Music di panel atas"""
        # Gunakan logic import yang sama agar masuk ke list audio_tracks
        self.on_import_audio_clicked()

    # --- TEMPLATE & PRESET HANDLERS ---
    def on_template_loaded(self, template_data):
        """Handler saat template JSON di-load"""
        # Bersihkan scene lama
        self.preview.scene.clear()
        self.layer_panel.list_layers.clear()
        
        # Load Background
        bg_data = template_data.get("background")
        if bg_data and bg_data.get("path"):
            self.engine.bg_layer.set_source(bg_data["path"])
            self.bg_item = BackgroundItem(bg_data["path"], self.preview.scene.sceneRect())
            self.bg_item.update_bg_settings(bg_data)
            self.preview.scene.addItem(self.bg_item)
            self.layer_panel.set_bg_values(bg_data)
            self.layer_panel.chk_bg_toggle.setChecked(True)
        
        # Load Layers
        for layer in template_data.get("layers", []):
            name = layer.get("name")
            path = layer.get("path")
            # Buat item
            self.on_create_visual_item(name.replace("FRAME ", ""), layer.get("shape", "portrait"))
            # Cari item yang baru dibuat
            for item in self.preview.scene.items():
                if isinstance(item, VideoItem) and item.name == name.replace("FRAME ", ""):
                    if path: item.set_content(path)
                    item.update_from_settings(layer)
                    break
        
        print(f"[TEMPLATE] Loaded {len(template_data.get('layers', []))} layers")

    def on_save_chroma_preset(self):
        """Menyimpan settingan layer saat ini sebagai preset"""
        selected = self.preview.scene.selectedItems()
        if not selected or not isinstance(selected[0], VideoItem):
            QMessageBox.warning(self.view, "Warning", "Pilih layer dulu!")
            return
            
        item = selected[0]
        name, ok = QInputDialog.getText(self.view, "Simpan Preset", "Nama Preset:")
        if ok and name:
            # Simpan item.settings ke JSON (Simulasi/Implementasi lanjutan)
            print(f"[PRESET] Saved {name}: {item.settings}")
            QMessageBox.information(self.view, "Info", "Preset tersimpan (Simulasi)")

    # --- RENDER LOGIC (UPDATED) ---
    def on_render_clicked(self):
        output_path, _ = QFileDialog.getSaveFileName(
            self.view, "Simpan Video", "project_output.mp4", "Video Files (*.mp4)"
        )
        if not output_path: return

        items_data = []
        scene_items = self.preview.scene.items()
        # Durasi harus valid
        total_duration = self.engine.duration if self.engine.duration > 0 else 5.0
        
        # Filter hanya item yang valid (VideoItem dan BackgroundItem)
        valid_items = [i for i in scene_items if isinstance(i, VideoItem)]

        for item in valid_items:
            is_background = isinstance(item, BackgroundItem)
            is_text = item.settings.get("content_type") == "text"
            
            # Skip item kosong
            if not is_text and not item.file_path:
                continue

            # --- CALCULATE DIMENSIONS ---
            # Kita perlu kirim ukuran visual akhir yang diinginkan ke FFmpeg
            # FFmpeg scale filter target
            
            frame_rect = item.rect()
            # Ukuran frame di canvas
            frame_w = int(frame_rect.width())
            frame_h = int(frame_rect.height())
            
            # Pastikan genap untuk codec H.264
            if frame_w % 2 != 0: frame_w += 1
            if frame_h % 2 != 0: frame_h += 1

            # Posisi di canvas
            if is_background:
                pos_x = item.settings.get('x', 0)
                pos_y = item.settings.get('y', 0)
                # rotasi background di handle via settings bukan transform item scene
                rot = 0 
            else:
                pos_x = int(item.x())
                pos_y = int(item.y())
                rot = int(item.rotation())

            item_data = {
                'path': item.file_path,
                'is_bg': is_background,
                'is_text': is_text,
                'text_pixmap': item.current_pixmap if is_text else None,
                
                # Koordinat Canvas
                'x': pos_x,
                'y': pos_y,
                
                # Ukuran Visual Akhir (Hasil Resize di GUI)
                'visual_w': frame_w,
                'visual_h': frame_h,
                'rot': rot, # Rotasi
                
                'z_value': item.zValue(),
                'start_time': 0,
                'end_time': total_duration
            }
            items_data.append(item_data)

        if not items_data: 
            QMessageBox.warning(self.view, "Render", "Tidak ada item di timeline untuk dirender.")
            return

        # Disable tombol
        self.layer_panel.render_tab.btn_render.setEnabled(False)
        self.layer_panel.render_tab.btn_render.setText("Rendering...")
        
        # Start Worker
        self.worker = RenderWorker(items_data, output_path, total_duration, audio_tracks=self.audio_tracks)
        self.worker.sig_progress.connect(self.on_render_progress)
        self.worker.sig_finished.connect(self.on_render_finished)
        self.worker.start()

    def on_render_progress(self, msg):
        print(f"[RENDER] {msg}")

    def on_render_finished(self, success, msg):
        self.layer_panel.render_tab.btn_render.setEnabled(True)
        self.layer_panel.render_tab.btn_render.setText("Render Video")
        if success:
            QMessageBox.information(self.view, "Sukses", msg)
        else:
            QMessageBox.critical(self.view, "Gagal", f"Error:\n{msg}")

    # --- LOGIC UTILITY & HELPERS (Existing) ---
    def recalculate_global_duration(self):
        max_duration = 0.0
        has_clips = False
        for item in self.preview.scene.items():
            if isinstance(item, VideoItem):
                if item.duration_s > max_duration:
                    max_duration = item.duration_s
                has_clips = True
        
        if max_duration == 0 and not has_clips:
            max_duration = 5.0
        
        self.engine.set_duration(max_duration)
        self.preview.timeline_slider.setRange(0, int(max_duration * 100))

    def on_create_visual_item(self, frame_code, shape="portrait"):
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
            
        self.bg_item = BackgroundItem(path, self.preview.scene.sceneRect())
        self.bg_item.seek_to(0)
        
        # Hitung geometri awal (Center Fit)
        geo_settings = BackgroundService.calculate_bg_geometry(
            self.bg_item.current_pixmap, 
            self.preview.scene.sceneRect()
        )
        if geo_settings:
            self.bg_item.update_bg_settings(geo_settings)
            self.layer_panel.set_bg_values(self.bg_item.settings)
            self.layer_panel.show_bg_controls(True)
        
        self.preview.scene.addItem(self.bg_item)
        self.preview.scene.update()
        self.recalculate_global_duration()

        def on_bg_properties_changed(self, data):
            if self.bg_item:
                self.bg_item.update_bg_settings(data)
            # FIX: Sinkronkan ke Preview Engine agar blur muncul di preview 
            if hasattr(self.engine, 'bg_layer'):
                self.engine.bg_layer.update_state(data)
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

    def on_add_text_clicked(self):
        """Membuat Item Teks Baru secara langsung"""
        # Frame code unik
        frame_code = f"TXT_{len(self.preview.scene.items())}"
        # Shape 'text' sebagai penanda
        item = VideoItem(frame_code, None, None, shape="text") 
        self.preview.scene.addItem(item)
        
        # Posisi Default agak tengah
        item.setPos(200, 400)
        # Set konten awal (ini akan memicu refresh_text_render internal item)
        item.set_text_content("New Text") 
        
        # Seleksi otomatis item baru
        self.preview.scene.clearSelection()
        item.setSelected(True)
        self.setting.set_values(item.settings)
        self.recalculate_global_duration()
        print(f"[MAIN] Text Created: {frame_code}")

    def on_add_paragraph_clicked(self):
        self._handle_text_input("Input Paragraf", "Paragraf:", True)

    def _handle_text_input(self, title, label, is_paragraph):
        selected = self.preview.scene.selectedItems()
        if not selected or not isinstance(selected[0], VideoItem): return
        target_item = selected[0]
        
        if is_paragraph:
            text, ok = QInputDialog.getMultiLineText(self.view, title, label)
        else:
            text, ok = QInputDialog.getText(self.view, title, label)
            
        if ok and text:
            target_item.set_text_content(text, is_paragraph=is_paragraph)
            self.setting.set_values(target_item.settings)
            self.recalculate_global_duration()
            self.preview.scene.update()

    def on_canvas_selection_update_ui(self):
        selected = self.preview.scene.selectedItems()
        is_video_item = False
        if selected and isinstance(selected[0], VideoItem):
            is_video_item = True
            item = selected[0]
            self.setting.set_values(item.settings)
            content_type = item.settings.get("content_type", "media")
            self.setting.set_active_tab_by_type(content_type)
            
            # Logic Lock
            is_locked = item.settings.get("lock", False)
            self.layer_panel.set_delete_enabled(not is_locked)
            self.layer_panel.set_reorder_enabled(not is_locked)
        else:
            self.layer_panel.set_delete_enabled(False)
            self.layer_panel.set_reorder_enabled(False)
        
        if hasattr(self.layer_panel, 'set_content_button_enabled'):
            self.layer_panel.set_content_button_enabled(is_video_item)
        else:
            self.layer_panel.btn_add_content.setEnabled(is_video_item)

    def on_canvas_item_moved(self, settings_data):
        self.setting.set_values(settings_data)

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
        if not self.engine.timer.isActive():
            self.engine.set_time(time_s)

    def update_ui_from_engine(self, t):
        self.preview.timeline_slider.blockSignals(True)
        self.preview.timeline_slider.setValue(int(t * 100))
        self.preview.timeline_slider.blockSignals(False)
        for item in self.preview.scene.items():
            if isinstance(item, VideoItem):
                item.seek_to(t)
            if self.bg_item:
                self.bg_item.seek_to(t)

    def update_play_button_icon(self, is_playing):
        icon = QStyle.SP_MediaPause if is_playing else QStyle.SP_MediaPlay
        self.preview.btn_play.setIcon(self.view.style().standardIcon(icon))

    def on_generate_caption(self, data):
        video_path = None
        for item in self.preview.scene.items():
            if isinstance(item, VideoItem):
                video_path = item.file_path
                break
        if not video_path:
            print("❌ Tidak ada video aktif")
            return
        base, ext = os.path.splitext(video_path)
        output = base + "_captioned.mp4"
        preset_map = {
            "Karaoke Highlight (Word-by-word)": "karaoke",
            "Custom (Manual)": "chunk",
            "Netflix Standard": "chunk",
            "Youtube Shorts (Yellow Bold)": "karaoke",
            "Cinematic Minimal": "chunk"
        }
        preset = preset_map.get(data["preset"], "karaoke")
        apply_caption(video_path=video_path, output_path=output, preset=preset)
        print(f"✅ Caption selesai: {output}")
        
    def on_bg_properties_changed(self, data):
        if self.bg_item:
            self.bg_item.update_bg_settings(data)
        if hasattr(self.engine, 'bg_layer'):
            self.engine.bg_layer.update_state(data)
        self.preview.scene.update()