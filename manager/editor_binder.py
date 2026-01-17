from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QAction, QKeySequence

class EditorBinder(QObject):
    """
    Glue Code: Menghubungkan Controller (Logic) dengan MainWindow (UI).
    Versi: DEBUG & SHORTCUT (Ctrl+E enabled)
    """
    def __init__(self, controller, main_window):
        super().__init__()
        self.c = controller
        self.ui = main_window
        
        self._connect_logic_to_ui()
        self._connect_ui_to_logic()

    def _connect_logic_to_ui(self):
        # ... (Logika Logic -> UI tetap sama) ...
        self.c.sig_layer_created.connect(self._on_layer_created)
        self.c.sig_layer_removed.connect(self._on_layer_removed)
        self.c.sig_layer_cleared.connect(self._on_layer_cleared)
        self.c.sig_property_changed.connect(self._on_property_changed)
        self.c.sig_selection_changed.connect(self._on_selection_changed)
        self.c.sig_layers_reordered.connect(self._on_layers_reordered)
        self.c.sig_status_message.connect(self.ui.status_bar.showMessage)
        self.c.sig_preview_update.connect(self._on_preview_update)

    def _connect_ui_to_logic(self):
        print("\n🔍 [BINDER] Checking UI Connections...")

        # 1. TIMELINE & LAYER ACTIONS
        if hasattr(self.ui.layer_panel, 'sig_request_seek'):
            self.ui.layer_panel.sig_request_seek.connect(self.c.seek_to)
            self.ui.layer_panel.sig_layer_selected.connect(self.c.select_layer)
            self.ui.layer_panel.sig_request_move.connect(self.c.move_layer_time)
            
            self.ui.layer_panel.sig_request_add.connect(self.c.add_new_layer)
            self.ui.layer_panel.sig_request_delete.connect(self.c.delete_current_layer)
            self.ui.layer_panel.sig_request_reorder.connect(self.c.reorder_layers)

        # 2. MEDIA INPUT
        self.ui.media_panel.sig_request_import.connect(self.c.add_new_layer)
        self.ui.audio_tab.sig_request_add_audio.connect(self.c.add_audio_layer)
        self.ui.template_tab.sig_apply_template.connect(self.c.apply_template)
        
        # 3. PROPERTY
        self.ui.setting_panel.sig_property_changed.connect(self.c.update_layer_property)
        self.ui.text_panel.sig_property_changed.connect(self.c.update_layer_property)
        
        # 4. SPECIAL FEATURES
        self.ui.chroma_panel.sig_apply_chroma.connect(self.c.apply_chroma_config)
        self.ui.chroma_panel.sig_remove_chroma.connect(self.c.remove_chroma_config)
        self.ui.caption_panel.sig_request_caption.connect(self.c.generate_auto_captions)
        
        # 5. GLOBAL ACTIONS
        self.ui.action_save.triggered.connect(self._on_menu_save)
        self.ui.action_open.triggered.connect(self._on_menu_open)
        self.ui.action_play.triggered.connect(self.c.toggle_play)
        
        # ======================================================================
        # 🔍 DEBUGGING EXPORT BUTTON
        # ======================================================================
        connected = False
        
        # Cek Menu Bar (action_export)
        if hasattr(self.ui, 'action_export'):
            print("✅ FOUND: self.ui.action_export -> Connected!")
            self.ui.action_export.triggered.connect(self._on_request_export)
            connected = True
        else:
            print("❌ MISSING: self.ui.action_export (Cek nama variabel di main_window.py)")

        # Cek Tombol Header (btn_export)
        if hasattr(self.ui, 'header_panel'):
            if hasattr(self.ui.header_panel, 'btn_export'):
                 print("✅ FOUND: self.ui.header_panel.btn_export -> Connected!")
                 self.ui.header_panel.btn_export.clicked.connect(self._on_request_export)
                 connected = True
            else:
                 print("❌ MISSING: btn_export di dalam header_panel (Cek nama variabel)")
        else:
            print("❌ MISSING: self.ui.header_panel")

        # 🚑 EMERGENCY SHORTCUT (Jalur Pintas)
        # Jika tombol tidak ketemu, kita buat shortcut keyboard Ctrl+E
        self.shortcut_export = QAction("Force Export", self.ui)
        self.shortcut_export.setShortcut(QKeySequence("Ctrl+E"))
        self.shortcut_export.triggered.connect(self._on_request_export)
        self.ui.addAction(self.shortcut_export)
        print("🚑 SHORTCUT: Tekan 'Ctrl+E' di keyboard untuk Export")
        
        print("--------------------------------------------------\n")

    # --- HANDLERS ---
    def _on_preview_update(self, t: float, active_ids: list):
        if hasattr(self.ui.preview_panel, "on_time_changed"):
            self.ui.preview_panel.on_time_changed(t)
        if hasattr(self.ui.preview_panel, "sync_layer_visibility"):
            self.ui.preview_panel.sync_layer_visibility(active_ids)
        if hasattr(self.ui.layer_panel, "update_playhead"):
            self.ui.layer_panel.update_playhead(t)

    def _on_layer_created(self, layer_data):
        self.ui.layer_panel.sync_all_layers(self.c.state.layers)
        self.ui.preview_panel.on_layer_created(layer_data)

    def _on_layer_removed(self, layer_id):
        self.ui.layer_panel.sync_all_layers(self.c.state.layers)
        self.ui.preview_panel.on_layer_removed(layer_id)
        
    def _on_layer_cleared(self):
        self.ui.layer_panel.clear_visual()
        self.ui.preview_panel.clear_visual()
        self.ui.setting_panel.clear_form()

    def _on_property_changed(self, layer_id, props):
        if "start_time" in props or "duration" in props:
             self.ui.layer_panel.sync_all_layers(self.c.state.layers)
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
        self.ui.layer_panel.sync_all_layers(self.c.state.layers)
        self.ui.preview_panel.on_layers_reordered(updates)

    def _on_menu_save(self):
        path, _ = QFileDialog.getSaveFileName(self.ui, "Save Project", "project.json", "JSON (*.json)")
        if path: self.c.save_project(path)

    def _on_menu_open(self):
        path, _ = QFileDialog.getOpenFileName(self.ui, "Open Project", "", "JSON (*.json)")
        if path: self.c.load_project(path)
        
    def _on_request_export(self):
        """Menangani klik tombol Export"""
        print("🚀 EXPORT TRIGGERED!") 
        
        path, _ = QFileDialog.getSaveFileName(
            self.ui, 
            "Export Video", 
            "output_video.mp4", 
            "MP4 Video (*.mp4)"
        )
        
        if path:
            config = {
                "path": path,
                "width": 1280, 
                "height": 720,
                "fps": 30
            }
            self.c.process_render(config)