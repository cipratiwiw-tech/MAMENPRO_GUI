# manager/editor_binder.py
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog # Boleh di Binder untuk dialog menu utama, atau pakai Service

class EditorBinder(QObject):
    def __init__(self, controller, main_window):
        super().__init__()
        self.c = controller
        self.ui = main_window
        
        self._connect_logic_to_ui()
        self._connect_ui_to_logic()

    def _connect_logic_to_ui(self):
        # CRUD Visual
        self.c.sig_layer_created.connect(self._on_layer_created)
        self.c.sig_layer_removed.connect(self._on_layer_removed)
        self.c.sig_layer_cleared.connect(self._on_layer_cleared)
        self.c.sig_property_changed.connect(self._on_property_changed)
        self.c.sig_selection_changed.connect(self._on_selection_changed)
        self.c.sig_layers_reordered.connect(self._on_layers_reordered)
        
        # Status
        self.c.sig_status_message.connect(self.ui.status_bar.showMessage)
        
        # [KRUSIAL] Jantung Aplikasi (Time & Visual Sync)
        # Controller mengirim (waktu, daftar_id_aktif)
        self.c.sig_preview_update.connect(self._on_preview_update)

    def _connect_ui_to_logic(self):
        # Panel Actions
        self.ui.media_panel.sig_request_import.connect(self.c.add_new_layer)
        self.ui.layer_panel.sig_request_add.connect(self.c.add_new_layer)
        self.ui.layer_panel.sig_request_delete.connect(self.c.delete_current_layer)
        self.ui.layer_panel.sig_layer_selected.connect(self.c.select_layer)
        self.ui.layer_panel.sig_request_reorder.connect(self.c.reorder_layers)
        
        # Property Panels
        self.ui.setting_panel.sig_property_changed.connect(self.c.update_layer_property)
        self.ui.text_panel.sig_property_changed.connect(self.c.update_layer_property)
        
        # Special Features
        self.ui.template_tab.sig_apply_template.connect(self.c.apply_template)
        self.ui.audio_tab.sig_request_add_audio.connect(self.c.add_audio_layer)
        self.ui.chroma_panel.sig_apply_chroma.connect(self.c.apply_chroma_config)
        self.ui.chroma_panel.sig_remove_chroma.connect(self.c.remove_chroma_config)
        self.ui.caption_panel.sig_request_caption.connect(self.c.generate_auto_captions)
        
        # Menu & Playback
        self.ui.action_save.triggered.connect(self._on_menu_save)
        self.ui.action_open.triggered.connect(self._on_menu_open)
        self.ui.action_play.triggered.connect(self.c.toggle_play)

    # --- HANDLERS ---    
    def _on_preview_update(self, t: float, active_ids: list):
        """
        Handler Detak Jantung.
        Diterima dari Controller setiap frame (misal 30fps).
        """
        # 1. Update Waktu di PreviewPanel (untuk animasi/scrubbing visual)
        # (Pastikan PreviewPanel punya method 'set_current_time' atau sejenisnya nanti)
        if hasattr(self.ui.preview_panel, "on_time_changed"):
            self.ui.preview_panel.on_time_changed(t)
            
        # 2. Update Visibilitas Layer
        # Binder memberitahu PreviewPanel: "Hanya ID ini yang boleh muncul!"
        # (Kita akan update PreviewPanel di langkah selanjutnya untuk support ini)
        if hasattr(self.ui.preview_panel, "sync_layer_visibility"):
            self.ui.preview_panel.sync_layer_visibility(active_ids)

    def _on_layer_created(self, layer_data):
        self.ui.layer_panel.add_item_visual(layer_data.id, layer_data.name)
        self.ui.preview_panel.on_layer_created(layer_data)

    def _on_layer_removed(self, layer_id):
        self.ui.layer_panel.remove_item_visual(layer_id)
        self.ui.preview_panel.on_layer_removed(layer_id)
        
    def _on_layer_cleared(self):
        self.ui.layer_panel.clear_visual()
        self.ui.preview_panel.clear_visual()
        self.ui.setting_panel.clear_form()

    def _on_property_changed(self, layer_id, props):
        self.ui.preview_panel.on_property_changed(layer_id, props)
        self.ui.setting_panel.update_form_visual(props)
        self.ui.text_panel.set_values(props)

    def _on_selection_changed(self, layer_data):
        if layer_data:
            self.ui.layer_panel.select_item_visual(layer_data.id)
            self.ui.preview_panel.on_selection_changed(layer_data)
            self.ui.setting_panel.update_form_visual(layer_data.properties)
            self.ui.text_panel.set_values(layer_data.properties)
        else:
            self.ui.setting_panel.clear_form()
            self.ui.preview_panel.on_selection_changed(None)

    def _on_layers_reordered(self, updates):
        self.ui.preview_panel.on_layers_reordered(updates)

    def _on_menu_save(self):
        path, _ = QFileDialog.getSaveFileName(self.ui, "Save Project", "project.json", "JSON (*.json)")
        if path: self.c.save_project(path)

    def _on_menu_open(self):
        path, _ = QFileDialog.getOpenFileName(self.ui, "Open Project", "", "JSON (*.json)")
        if path: self.c.load_project(path)