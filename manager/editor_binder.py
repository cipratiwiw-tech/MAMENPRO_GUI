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
        # 1. Saat Layer Dibuat (Logic) -> Update Visual (UI)
        self.c.sig_layer_created.connect(self._on_layer_created)
        
        # 2. Saat Layer Dihapus (Logic) -> Update Visual (UI)
        self.c.sig_layer_removed.connect(self._on_layer_removed)
        
        # 3. Saat Properti Berubah (Logic) -> Update Form & Canvas (UI)
        self.c.sig_property_changed.connect(self._on_property_changed)
        
        # 4. Saat Selection Berubah (Logic) -> Update Highlight & Form (UI)
        self.c.sig_selection_changed.connect(self._on_selection_changed)

    def _connect_ui_to_logic(self):
        # 1. Layer Panel Requests
        self.ui.layer_panel.sig_request_add.connect(self.c.add_new_layer)
        self.ui.layer_panel.sig_request_delete.connect(self.c.delete_current_layer)
        self.ui.layer_panel.sig_layer_selected.connect(self.c.select_layer)
        
        # 2. Setting Panel Requests
        self.ui.setting_panel.sig_property_changed.connect(self.c.update_layer_property)
        
        # 3. Media Panel Requests
        self.ui.media_panel.sig_request_import.connect(self.c.add_new_layer)

    # --- GLUE METHODS (Penerjemah Data Logic ke Format UI) ---

    def _on_layer_created(self, layer_data):
        # Beritahu LayerPanel: "Ada item baru nih, namanya X, ID-nya Y"
        self.ui.layer_panel.add_item_visual(layer_data.id, layer_data.name)
        # Beritahu PreviewPanel: "Render item ini"
        self.ui.preview_panel.on_layer_created(layer_data)

    def _on_layer_removed(self, layer_id):
        self.ui.layer_panel.remove_item_visual(layer_id)
        self.ui.preview_panel.on_layer_removed(layer_id)

    def _on_property_changed(self, layer_id, props):
        # Update Canvas
        self.ui.preview_panel.on_property_changed(layer_id, props)
        # Jika layer ini sedang disorot di SettingPanel, update juga angkanya
        # (Idealnya cek ID dulu, tapi untuk simplifikasi kita update saja)
        self.ui.setting_panel.update_form_visual(props)

    def _on_selection_changed(self, layer_data):
        if layer_data:
            # Highlight di List
            self.ui.layer_panel.select_item_visual(layer_data.id)
            # Isi Form
            self.ui.setting_panel.update_form_visual(layer_data.properties)
            # Highlight di Canvas
            self.ui.preview_panel.on_selection_changed(layer_data)
        else:
            self.ui.setting_panel.clear_form()
            self.ui.preview_panel.on_selection_changed(None)