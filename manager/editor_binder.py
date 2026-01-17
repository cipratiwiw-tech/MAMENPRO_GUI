from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import QObject

class EditorBinder(QObject):
    """
    Penghubung antara Logic (Controller) dan Presentation (UI).
    Tanggung Jawab: Dependency Injection & Signal Wiring.
    """
    def __init__(self, controller, main_window):
        super().__init__()
        self.c = controller
        self.ui = main_window
        
        # =========================================================
        # 1. DEPENDENCY INJECTION (CONTRACT ENFORCEMENT)
        # =========================================================
        if hasattr(self.c, 'video_service') and hasattr(self.ui, 'preview_panel'):
            print("🔗 [BINDER] Injecting Shared VideoService to PreviewPanel...")
            self.ui.preview_panel.set_video_service(self.c.video_service)
        else:
            print("❌ [BINDER] FATAL: VideoService injection failed!")

        # 2. Wiring
        self._connect_logic_to_ui()
        self._connect_ui_to_logic()

    def _connect_logic_to_ui(self):
        # PREVIEW LOOP
        self.c.sig_preview_update.connect(self._on_preview_update)
        
        # CRUD EVENTS
        self.c.sig_layer_created.connect(self._on_layer_created)
        self.c.sig_layer_removed.connect(self._on_layer_removed)
        self.c.sig_selection_changed.connect(self._on_selection_changed)
        self.c.sig_property_changed.connect(self._on_property_changed)

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
        """
        Handler Frame-by-Frame.
        Menerima 't' dan 'active_ids' dari Controller, lalu menyuruh UI update.
        """
        # 1. Update Visibility Layer (Siapa yang muncul?)
        if hasattr(self.ui.preview_panel, "sync_layer_visibility"):
            self.ui.preview_panel.sync_layer_visibility(active_ids)
        
        # 2. Update Content Frame (Video bergerak sesuai 't')
        if hasattr(self.ui.preview_panel, "on_time_changed"):
            self.ui.preview_panel.on_time_changed(t)
            
        # 3. Update Playhead Timeline
        if hasattr(self.ui.layer_panel, "update_playhead"):
            self.ui.layer_panel.update_playhead(t)

    def _on_layer_created(self, layer_data):
        self.ui.preview_panel.on_layer_created(layer_data)

    def _on_layer_removed(self, layer_id):
        self.ui.preview_panel.on_layer_removed(layer_id)

    def _on_selection_changed(self, layer_data):
        self.ui.preview_panel.on_selection_changed(layer_data)

    def _on_property_changed(self, layer_id, props):
        self.ui.preview_panel.on_property_changed(layer_id, props)
        
    def _on_menu_save(self):
        print("[BINDER] Save requested")
        # panggil controller
        self.c.save_project()

    def _on_menu_open(self):
        print("[BINDER] Open requested")
        self.c.open_project()

    def _on_request_export(self):
        print("[BINDER] Export requested")
        self.c.export_project()