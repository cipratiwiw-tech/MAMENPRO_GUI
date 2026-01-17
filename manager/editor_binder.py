# manager/editor_binder.py
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog

class EditorBinder(QObject):
    """
    Penghubung antara Logic (Controller) dan Presentation (UI).
    """
    def __init__(self, controller, main_window):
        super().__init__()
        self.c = controller
        self.ui = main_window
        
        # 1. Injection Service ke Preview Panel
        if hasattr(self.c, 'video_service') and hasattr(self.ui, 'preview_panel'):
            print("🔗 [BINDER] Injecting VideoService to PreviewPanel...")
            self.ui.preview_panel.set_video_service(self.c.video_service)
        
        # 2. Wiring Signals
        self._connect_logic_to_ui()
        self._connect_ui_to_logic()

    def _connect_logic_to_ui(self):
        # Update Visual Preview
        self.c.sig_preview_update.connect(self._on_preview_update)
        self.c.sig_status_message.connect(self.ui.status_bar.showMessage)
        
        # CRUD Events
        self.c.sig_layer_created.connect(self._on_layer_created)
        self.c.sig_layer_removed.connect(self._on_layer_removed)
        self.c.sig_layer_cleared.connect(self._on_layer_cleared)
        
        # Selection & Property Sync
        self.c.sig_selection_changed.connect(self._on_selection_changed)
        self.c.sig_property_changed.connect(self._on_property_changed)
        
        # Timeline Sync
        if hasattr(self.ui, 'layer_panel'):
            self.c.sig_layers_reordered.connect(lambda _: self.ui.layer_panel.sync_all_layers(self.c.state.layers))
            self.c.sig_layer_cleared.connect(self.ui.layer_panel.clear_visual)

    def _connect_ui_to_logic(self):
        # 1. TIMELINE ACTIONS
        if hasattr(self.ui, 'layer_panel'):
            lp = self.ui.layer_panel
            lp.sig_request_seek.connect(self.c.seek_to)
            lp.sig_layer_selected.connect(self.c.select_layer)
            lp.sig_request_move.connect(self.c.move_layer_time)
            lp.sig_request_add.connect(self.c.add_new_layer)
            lp.sig_request_delete.connect(self.c.delete_current_layer)
            lp.sig_request_reorder.connect(self.c.reorder_layers)

        # 2. PREVIEW PANEL INTERACTION (✅ WAJIB ADA UNTUK DRAG & DROP)

        if hasattr(self.ui, 'preview_panel'):
            pp = self.ui.preview_panel
            pp.sig_property_changed.connect(self.c.update_layer_property)
            pp.sig_layer_selected.connect(self.c.select_layer)
            
            # 🔥 TAMBAHKAN INI: Agar tombol Delete & Menu Context berfungsi
            if hasattr(pp, 'sig_request_delete'):
                pp.sig_request_delete.connect(lambda lid: self.c.delete_current_layer())

        # 3. MEDIA & ASSETS
        self.ui.media_panel.sig_request_import.connect(self.c.add_new_layer)
        self.ui.audio_tab.sig_request_add_audio.connect(self.c.add_audio_layer)
        self.ui.template_tab.sig_apply_template.connect(self.c.apply_template)
        
        # 4. PROPERTIES (PANEL KANAN)
        self.ui.setting_panel.sig_property_changed.connect(self.c.update_layer_property)
        self.ui.text_panel.sig_property_changed.connect(self.c.update_layer_property)
        
        # 5. RENDER (✅ NAMA SINYAL DIPERBAIKI)
        self.ui.render_tab.sig_start_render.connect(self.c.process_render)
        
        # 6. MENU ACTIONS
        self.ui.action_save.triggered.connect(self._on_menu_save)
        self.ui.action_open.triggered.connect(self._on_menu_open)
        self.ui.action_play.triggered.connect(self.c.toggle_play)

        # 7. CAPTION & CHROMA
        self.ui.caption_panel.sig_request_caption.connect(self.c.generate_auto_captions)
        self.ui.chroma_panel.sig_apply_chroma.connect(self.c.apply_chroma_config)
        self.ui.chroma_panel.sig_remove_chroma.connect(self.c.remove_chroma_config)

    # --- HANDLERS ---

    def _on_preview_update(self, t, active_ids):
        self.ui.preview_panel.sync_layer_visibility(active_ids)
        self.ui.preview_panel.on_time_changed(t)
        self.ui.layer_panel.update_playhead(t)

    def _on_layer_created(self, layer_data):
        self.ui.preview_panel.on_layer_created(layer_data)
        self.ui.layer_panel.sync_all_layers(self.c.state.layers)

    def _on_layer_removed(self, layer_id):
        self.ui.preview_panel.on_layer_removed(layer_id)
        self.ui.layer_panel.sync_all_layers(self.c.state.layers)

    def _on_layer_cleared(self):
        self.ui.preview_panel.items_map.clear()
        self.ui.preview_panel.scene.clear()
        # Re-add canvas frame & grid
        if hasattr(self.ui.preview_panel, 'canvas_frame'):
            self.ui.preview_panel.scene.addItem(self.ui.preview_panel.canvas_frame)

    def _on_selection_changed(self, layer_data):
        self.ui.preview_panel.on_selection_changed(layer_data)
        props = layer_data.properties if layer_data else {}
        self.ui.setting_panel.set_values(props)
        self.ui.text_panel.set_values(props)
        if layer_data:
            self.ui.layer_panel.select_item_visual(layer_data.id)

    def _on_property_changed(self, layer_id, props):
        self.ui.preview_panel.on_property_changed(layer_id, props)

    def _on_menu_save(self):
        path, _ = QFileDialog.getSaveFileName(self.ui, "Save Project", "", "JSON Files (*.json)")
        if path: self.c.save_project(path)

    def _on_menu_open(self):
        path, _ = QFileDialog.getOpenFileName(self.ui, "Open Project", "", "JSON Files (*.json)")
        if path: self.c.load_project(path)