# manager/editor_binder.py
from PySide6.QtCore import QObject

class EditorBinder(QObject):
    """
    Kelas ini bertanggung jawab menghubungkan (Wiring) 
    antara Logic (Controller) dan Visual (MainWindow).
    MainWindow tidak boleh tahu logic, Controller tidak boleh tahu UI.
    """
    def __init__(self, controller, main_window):
        super().__init__()
        self.c = controller
        self.ui = main_window
        
        self._connect_signals()

    def _connect_signals(self):
        # ==========================================
        # 1. CONTROLLER -> UI (Output Logic ke Visual)
        # ==========================================
        
        # Saat Data Layer bertambah -> Update List di LayerPanel
        self.c.sig_layer_created.connect(self._on_layer_created_visual)
        
        # Saat Data Layer dihapus -> Hapus item di LayerPanel
        self.c.sig_layer_removed.connect(self._on_layer_removed_visual)
        
        # Saat Selection berubah di Logic -> Update UI (Highlight & Form Value)
        self.c.sig_selection_changed.connect(self._on_selection_logic_changed)

        # ==========================================
        # 2. UI -> CONTROLLER (Input User ke Logic)
        # ==========================================
        
        # User geser slider di SettingPanel -> Update Logic
        self.ui.setting_panel.on_setting_change.connect(self.c.update_layer_property)
        
        # User klik "New Layer" di LayerPanel -> Panggil Logic
        self.ui.layer_panel.sig_layer_created.connect(self._on_ui_request_new_layer)
        
        # User klik item di List -> Select di Logic
        self.ui.layer_panel.sig_layer_selected.connect(self.c.select_layer)
        
        # User klik delete -> Delete di Logic
        self.ui.layer_panel.sig_delete_layer.connect(self.c.delete_current_layer)
        
        # [BARU] Media Panel -> Controller
        # Saat MediaPanel teriak "User mau import!", Controller lakukan "add_new_layer"
        self.ui.media_panel.sig_request_import.connect(self.c.add_new_layer)

    # --- GLUE LOGIC (Jembatan Data) ---
    # Di sinilah "Pengetahuan Detail" disimpan, bukan di MainWindow

    def _on_layer_created_visual(self, layer_data):
        # Binder tahu bahwa LayerPanel butuh 'name' dari object data
        self.ui.layer_panel.add_layer_item_custom(layer_data.name)

    def _on_layer_removed_visual(self, layer_id):
        # Binder tahu cara menyuruh LayerPanel menghapus item
        # (Anda perlu implementasikan remove_layer_item_by_code di LayerPanel nanti)
        # self.ui.layer_panel.remove_layer_item_by_code(layer_id)
        pass 

    def _on_selection_logic_changed(self, layer_data):
        # 1. Update List Selection
        if layer_data:
            self.ui.layer_panel.select_layer_by_code(layer_data.id)
            # 2. Update Form Values
            self.ui.setting_panel.set_values(layer_data.properties)
        else:
            self.ui.setting_panel.set_values({})

    def _on_ui_request_new_layer(self, code, shape):
        # Binder yang menentukan "Default layer type" adalah text
        # MainWindow tidak perlu tahu ini.
        self.c.add_new_layer("text")