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
        # ... (Koneksi lama layer_created, dll TETAP SAMA) ...
        self.c.sig_layer_created.connect(self._on_layer_created)
        self.c.sig_layer_removed.connect(self._on_layer_removed)
        self.c.sig_property_changed.connect(self._on_property_changed)
        self.c.sig_selection_changed.connect(self._on_selection_changed)
        
        # [BARU] Clear Canvas saat Load Project
        self.c.sig_layer_cleared.connect(self._on_layer_cleared)

        # [UPDATE] Status Message -> Real UI Status Bar
        self.c.sig_status_message.connect(self.ui.status_bar.showMessage)
        
        # [BARU] Reorder Event
        self.c.sig_layers_reordered.connect(self._on_layers_reordered)

    def _connect_ui_to_logic(self):
        # ... (Koneksi panel lama TETAP SAMA) ...
        self.ui.media_panel.sig_request_import.connect(self.c.add_new_layer)
        self.ui.layer_panel.sig_request_add.connect(self.c.add_new_layer)
        self.ui.layer_panel.sig_request_delete.connect(self.c.delete_current_layer)
        self.ui.layer_panel.sig_layer_selected.connect(self.c.select_layer)
        self.ui.setting_panel.sig_property_changed.connect(self.c.update_layer_property)
        self.ui.text_panel.sig_property_changed.connect(self.c.update_layer_property)
        self.ui.template_tab.sig_apply_template.connect(self.c.apply_template)
        self.ui.render_tab.sig_request_render.connect(self.c.process_render)

        # [BARU] Menu Bar Actions
        self.ui.action_save.triggered.connect(self._on_menu_save)
        self.ui.action_open.triggered.connect(self._on_menu_open)
        
        # [BARU] Request dari LayerPanel
        self.ui.layer_panel.sig_request_reorder.connect(self.c.reorder_layers)
        
        # [BARU] Audio Tab -> Controller
        self.ui.audio_tab.sig_request_add_audio.connect(self.c.add_audio_layer)
        
        # [BARU] Chroma Panel -> Controller
        self.ui.chroma_panel.sig_apply_chroma.connect(self.c.apply_chroma_config)
        self.ui.chroma_panel.sig_remove_chroma.connect(self.c.remove_chroma_config)
        
        # [BARU] Caption Panel -> Controller
        self.ui.caption_panel.sig_request_caption.connect(self.c.generate_auto_captions)

    # --- ACTION HANDLERS (GLUE) ---

    def _on_menu_save(self):
        # UX Decision: Buka dialog di sini (atau pakai service), lalu lempar path ke Controller
        path, _ = QFileDialog.getSaveFileName(self.ui, "Save Project", "my_project.json", "JSON (*.json)")
        if path:
            self.c.save_project(path)

    def _on_menu_open(self):
        path, _ = QFileDialog.getOpenFileName(self.ui, "Open Project", "", "JSON (*.json)")
        if path:
            self.c.load_project(path)

    def _on_layer_cleared(self):
        # UI List: Bersihkan via method resmi (yang sudah kita buat sebelumnya)
        self.ui.layer_panel.clear_visual()
        
        # Preview: Bersihkan via method resmi [UPDATED]
        self.ui.preview_panel.clear_visual()
        
        # Reset form properties
        self.ui.setting_panel.clear_form()
        self.ui.text_panel.set_values({})
        
    # ... (Glue methods lain _on_layer_created dll TETAP SAMA) ...
    def _on_layer_created(self, layer_data):
        self.ui.layer_panel.add_item_visual(layer_data.id, layer_data.name)
        self.ui.preview_panel.on_layer_created(layer_data)

    def _on_layer_removed(self, layer_id):
        self.ui.layer_panel.remove_item_visual(layer_id)
        self.ui.preview_panel.on_layer_removed(layer_id)

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
            if layer_data.type == 'text':
                self.ui.right_tabs.setCurrentWidget(self.ui.text_panel)
            else:
                self.ui.right_tabs.setCurrentWidget(self.ui.setting_panel)
        else:
            self.ui.setting_panel.clear_form()
            self.ui.preview_panel.on_selection_changed(None)
            
    def _on_layers_reordered(self, updates):
        # Beritahu Preview Panel
        self.ui.preview_panel.on_layers_reordered(updates)
        
        # Catatan: LayerPanel UI sudah berubah duluan karena user yang drag-drop.
        # Jadi kita TIDAK perlu refresh list LayerPanel, kecuali kita mau force sync.
        # Untuk saat ini, biarkan UI List apa adanya karena asumsinya user sudah melihat perubahannya.