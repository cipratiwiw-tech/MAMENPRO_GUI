# manager/editor_binder.py
from PySide6.QtCore import QObject

class EditorBinder(QObject):
    def __init__(self, controller, main_window):
        super().__init__()
        self.c = controller
        self.ui = main_window
        
        self._connect_logic_to_ui()
        self._connect_ui_to_logic()

    def _connect_logic_to_ui(self):
        # ... (Koneksi sebelumnya tetap ada: layer created, removed, prop changed) ...
        self.c.sig_layer_created.connect(self._on_layer_created)
        self.c.sig_layer_removed.connect(self._on_layer_removed)
        self.c.sig_property_changed.connect(self._on_property_changed)
        self.c.sig_selection_changed.connect(self._on_selection_changed)
        
        # [BARU] Status Message (misal untuk Toast/Log di UI)
        self.c.sig_status_message.connect(lambda msg: print(f"[UI NOTIFY]: {msg}"))

    def _connect_ui_to_logic(self):
        # ... (Koneksi sebelumnya tetap ada: media, layer, setting, text panel) ...
        self.ui.media_panel.sig_request_import.connect(self.c.add_new_layer)
        self.ui.layer_panel.sig_request_add.connect(self.c.add_new_layer)
        self.ui.layer_panel.sig_request_delete.connect(self.c.delete_current_layer)
        self.ui.layer_panel.sig_layer_selected.connect(self.c.select_layer)
        self.ui.setting_panel.sig_property_changed.connect(self.c.update_layer_property)
        self.ui.text_panel.sig_property_changed.connect(self.c.update_layer_property)
        
        # [BARU] WIRING UNTUK TAB BARU
        # Template Tab -> Controller Delegate
        self.ui.template_tab.sig_apply_template.connect(self.c.apply_template)
        
        # Render Tab -> Controller Delegate
        self.ui.render_tab.sig_request_render.connect(self.c.process_render)

    # ... (Glue methods: _on_layer_created, dll tetap sama) ...
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
            # UX: Auto switch tab
            if layer_data.type == 'text':
                self.ui.right_tabs.setCurrentWidget(self.ui.text_panel)
            else:
                self.ui.right_tabs.setCurrentWidget(self.ui.setting_panel)
        else:
            self.ui.setting_panel.clear_form()
            self.ui.preview_panel.on_selection_changed(None)