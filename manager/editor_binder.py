# manager/editor_binder.py
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QAction, QKeySequence

class EditorBinder(QObject):
    """
    Penghubung antara Logic (Controller) dan Presentation (UI).
    Memastikan data mengalir lancar dari Controller ke UI tanpa UI tau logic.
    """
    def __init__(self, controller, main_window):
        super().__init__()
        self.c = controller
        self.ui = main_window
        
        # =========================================================
        # 1. DEPENDENCY INJECTION (CRITICAL FOR PREVIEW)
        # =========================================================
        if hasattr(self.c, 'video_service') and hasattr(self.ui, 'preview_panel'):
            print("🔗 [BINDER] Injecting VideoService to PreviewPanel...")
            # Ini KUNCI agar PreviewPanel tidak 'Zonk'
            self.ui.preview_panel.set_video_service(self.c.video_service)
        else:
            print("❌ [BINDER] FATAL: VideoService injection failed!")

        # 2. Wiring Signals
        self._connect_logic_to_ui()
        self._connect_ui_to_logic()

    def _connect_logic_to_ui(self):
        # --- CORE PREVIEW LOOP ---
        # Saat Controller 'tick', UI harus update visual
        self.c.sig_preview_update.connect(self._on_preview_update)
        self.c.sig_status_message.connect(self.ui.status_bar.showMessage)
        
        # --- CRUD EVENTS ---
        self.c.sig_layer_created.connect(self._on_layer_created)
        self.c.sig_layer_removed.connect(self._on_layer_removed)
        self.c.sig_layer_cleared.connect(self._on_layer_cleared)
        
        # --- SELECTION & PROPERTY ---
        self.c.sig_selection_changed.connect(self._on_selection_changed)
        self.c.sig_property_changed.connect(self._on_property_changed)
        
        # --- TIMELINE SYNC ---
        if hasattr(self.ui, 'layer_panel'):
            self.c.sig_layers_reordered.connect(lambda _: self.ui.layer_panel.sync_all_layers(self.c.state.layers))
            # Saat load project, sync total
            self.c.sig_layer_cleared.connect(self.ui.layer_panel.clear_visual)

    def _connect_ui_to_logic(self):
        # 1. TIMELINE ACTIONS
        if hasattr(self.ui, 'layer_panel'):
            lp = self.ui.layer_panel
            lp.sig_request_seek.connect(self.c.seek_to)
            lp.sig_layer_selected.connect(self.c.select_layer)
            lp.sig_request_move.connect(self.c.move_layer_time)
            
            # Legacy signals from panel
            lp.sig_request_add.connect(self.c.add_new_layer)
            lp.sig_request_delete.connect(self.c.delete_current_layer)
            lp.sig_request_reorder.connect(self.c.reorder_layers)

        # 2. MEDIA INPUT & ASSETS
        self.ui.media_panel.sig_request_import.connect(self.c.add_new_layer)
        self.ui.audio_tab.sig_request_add_audio.connect(self.c.add_audio_layer)
        self.ui.template_tab.sig_apply_template.connect(self.c.apply_template)
        
        # 3. PROPERTIES
        self.ui.setting_panel.sig_property_changed.connect(self.c.update_layer_property)
        self.ui.text_panel.sig_property_changed.connect(self.c.update_layer_property)
        
        # 4. RENDER / EXPORT
        self.ui.render_tab.sig_request_render.connect(self.c.process_render)
        
        # 5. MENU ACTIONS
        self.ui.action_save.triggered.connect(self._on_menu_save)
        self.ui.action_open.triggered.connect(self._on_menu_open)
        self.ui.action_play.triggered.connect(self.c.toggle_play)

        # 6. CAPTION & CHROMA
        self.ui.caption_panel.sig_request_caption.connect(self.c.generate_auto_captions)
        self.ui.chroma_panel.sig_apply_chroma.connect(self.c.apply_chroma_config)
        self.ui.chroma_panel.sig_remove_chroma.connect(self.c.remove_chroma_config)

    # --- HANDLERS (GLUE CODE) ---

    def _on_preview_update(self, t: float, active_ids: list):
        """
        Handler Pusat: Controller bilang 'Waktu T, Layer X,Y,Z aktif'
        Binder menyuruh UI untuk menyesuaikan diri.
        """
        # 1. Update siapa yang terlihat di PreviewPanel
        self.ui.preview_panel.sync_layer_visibility(active_ids)
        
        # 2. Update konten gambar di PreviewPanel (fetch frame)
        self.ui.preview_panel.on_time_changed(t)
        
        # 3. Update garis playhead di Timeline
        self.ui.layer_panel.update_playhead(t)

    def _on_layer_created(self, layer_data):
        # PreviewPanel perlu bikin item visual dummy
        self.ui.preview_panel.on_layer_created(layer_data)
        # Timeline perlu bikin clip visual
        # Kita trigger sync total untuk safety (atau bisa add single)
        self.ui.layer_panel.sync_all_layers(self.c.state.layers)

    def _on_layer_removed(self, layer_id):
        self.ui.preview_panel.on_layer_removed(layer_id)
        # Sync timeline
        self.ui.layer_panel.sync_all_layers(self.c.state.layers)

    def _on_layer_cleared(self):
        # Saat File > New Project
        self.ui.preview_panel.items_map.clear()
        self.ui.preview_panel.scene.clear()
        self.ui.preview_panel.active_gizmo = None
        # Re-init overlay
        self.ui.preview_panel._init_overlays() 

    def _on_selection_changed(self, layer_data):
        # Beritahu Preview (untuk Gizmo)
        self.ui.preview_panel.on_selection_changed(layer_data)
        # Beritahu Property Panels
        props = layer_data.properties if layer_data else {}
        self.ui.setting_panel.set_values(props)
        self.ui.text_panel.set_values(props)
        # Beritahu Timeline (Highlight)
        if layer_data:
            self.ui.layer_panel.select_item_visual(layer_data.id)

    def _on_property_changed(self, layer_id, props):
        self.ui.preview_panel.on_property_changed(layer_id, props)

    def _on_menu_save(self):
        path, _ = QFileDialog.getSaveFileName(self.ui, "Save Project", "", "JSON Files (*.json)")
        if path:
            self.c.save_project(path)

    def _on_menu_open(self):
        path, _ = QFileDialog.getOpenFileName(self.ui, "Open Project", "", "JSON Files (*.json)")
        if path:
            self.c.load_project(path)