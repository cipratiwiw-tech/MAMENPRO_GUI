from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QGridLayout, QLabel, QPushButton, QCheckBox, 
                             QSpinBox, QListWidget, QFrame, QScrollArea, QComboBox, QTabWidget, QListWidgetItem, QMenu)
from PySide6.QtCore import Qt, Signal

# Import Panel-Panel Tab
from gui.left_panel.template_tab import TemplateTab
from gui.left_panel.presetchroma_panel import PresetChromaPanel
from gui.left_panel.audio_tab import AudioTab
from gui.left_panel.render_tab import RenderTab

class LayerPanel(QWidget):
    # Sinyal
    sig_layer_created = Signal(str, str)      
    sig_layer_selected = Signal(str)     
    sig_layer_reordered = Signal(int, int) 
    sig_delete_layer = Signal(str)       
    sig_bg_changed = Signal(dict)          
    sig_bg_toggle = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(320)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- SISTEM TAB ---
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # 1. Tab Editor
        self.tab_editor = QWidget()
        self._init_editor_ui()
        
        self.tab_templates = TemplateTab()
        self.tab_chroma = PresetChromaPanel()
        self.tab_audio = AudioTab()
        
        self.tabs.addTab(self.tab_editor, "Editor")
        self.tabs.addTab(self.tab_templates, "Templates")
        self.tabs.addTab(self.tab_chroma, "Chroma")
        self.tabs.addTab(self.tab_audio, "Audio")

        self._connect_internal_signals()

    def _init_editor_ui(self):
        layout = QVBoxLayout(self.tab_editor)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 1. ATAS: AUDIO & BACKGROUND
        top_group_container = QWidget()
        top_group_layout = QVBoxLayout(top_group_container)
        top_group_layout.setContentsMargins(0, 0, 0, 0)

        # Audio
        self.group_audio = QGroupBox("AUDIO SETTINGS")
        audio_grid = QGridLayout(self.group_audio)
        self.btn_add_audio = QPushButton("Add Music")
        self.chk_mute = QCheckBox("Mute")
        self.spn_volume = QSpinBox(); self.spn_volume.setRange(0, 100); self.spn_volume.setValue(100)
        audio_grid.addWidget(self.btn_add_audio, 0, 0, 1, 2)
        audio_grid.addWidget(QLabel("Vol:"), 1, 0); audio_grid.addWidget(self.spn_volume, 1, 1)
        audio_grid.addWidget(self.chk_mute, 1, 2)
        top_group_layout.addWidget(self.group_audio)

        # Background
        self.group_bg = QGroupBox("BACKGROUND SETTING")
        self.group_bg.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #636e72; margin-top: 5px; }")
        bg_main_layout = QVBoxLayout(self.group_bg)
        bg_main_layout.setSpacing(5)
        
        # --- [MODIFIKASI LAYOUT BARIS 1] ---
        row1_layout = QHBoxLayout()
        
        # 1. Tombol Add (Stretch dikurangi jadi 3 biar muat)
        self.btn_add_bg = QPushButton("Add Background")
        self.btn_add_bg.setStyleSheet("background-color: #2d3436; color: white;")
        
        # 2. Tombol Lock (BARU)
        self.chk_bg_lock = QCheckBox("🔒")
        self.chk_bg_lock.setToolTip("Lock Position & Zoom")
        self.chk_bg_lock.setStyleSheet("font-weight: bold; color: #dfe6e9;")
        self.chk_bg_lock.toggled.connect(self._on_bg_lock_toggled) # Connect ke fungsi baru
        
        # 3. Tombol Toggle ON/OFF
        self.chk_bg_toggle = QCheckBox("ON")
        self.chk_bg_toggle.setChecked(True)
        self.chk_bg_toggle.setStyleSheet("font-weight: bold;")
        self.chk_bg_toggle.toggled.connect(self._on_bg_toggled_internal)
        
        # Susun Layout (Add=3, Lock=1, Toggle=1)
        row1_layout.addWidget(self.btn_add_bg, stretch=3)
        row1_layout.addWidget(self.chk_bg_lock, stretch=1)
        row1_layout.addWidget(self.chk_bg_toggle, stretch=1)
        
        bg_main_layout.addLayout(row1_layout)

        bg_grid = QGridLayout()
        bg_grid.setSpacing(5)
        bg_grid.setContentsMargins(0, 0, 0, 0)

        self.spin_bg_x = self._create_spinbox("Posisi X", -2000, 2000, 0)
        self.spin_bg_y = self._create_spinbox("Posisi Y", -2000, 2000, 0)
        self.spin_bg_scale = self._create_spinbox("Zoom (Scale)", 1, 1000, 100)
        self.spn_vignette = self._create_spinbox("Efek Vignette (0-100)", 0, 100, 0)
        self.spn_blur = self._create_spinbox("Efek Blur (0-50)", 0, 50, 0) # Max 50 biar ga berat

        def add_cell(row, col, label_text, widget):
            container = QWidget()
            h_layout = QHBoxLayout(container)
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(2)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #b2bec3; font-size: 10px;")
            lbl.setFixedWidth(25)
            h_layout.addWidget(lbl); h_layout.addWidget(widget)
            bg_grid.addWidget(container, row, col)

        add_cell(0, 0, "X:", self.spin_bg_x)
        add_cell(0, 1, "Y:", self.spin_bg_y)
        add_cell(0, 2, "Zm:", self.spin_bg_scale)
        add_cell(1, 0, "Vig:", self.spn_vignette)
        add_cell(1, 1, "Blr:", self.spn_blur)
        bg_grid.addWidget(QLabel(""), 1, 2) 

        bg_main_layout.addLayout(bg_grid)
        top_group_layout.addWidget(self.group_bg)
        layout.addWidget(top_group_container)

        # 2. TENGAH: TIMELINE LAYERS
        self.mid_container = QGroupBox("TIMELINE LAYERS")
        mid_layout = QVBoxLayout(self.mid_container)

        self.list_layers = QListWidget()
        mid_layout.addWidget(self.list_layers)

        layer_btns = QHBoxLayout()
        self.btn_new = QPushButton("+ New Frame")
        self.btn_new.setStyleSheet("background-color: #0984e3; color: white; font-weight: bold; padding: 5px;")
        
        self.menu_new = QMenu(self)
        self.menu_new.setStyleSheet("QMenu { background-color: #2d3436; color: white; } QMenu::item:selected { background-color: #0984e3; }")
        self.menu_new.addAction("Portrait (9:16)", lambda: self.action_add_new("portrait"))
        self.menu_new.addAction("Landscape (16:9)", lambda: self.action_add_new("landscape"))
        self.menu_new.addAction("Kotak / Square (1:1)", lambda: self.action_add_new("square"))
        self.menu_new.addAction("Bulat / Circle", lambda: self.action_add_new("circle"))
        self.btn_new.setMenu(self.menu_new)
        
        self.btn_del = QPushButton("Del") 
        self.btn_up = QPushButton("▲"); self.btn_up.setFixedWidth(30)
        self.btn_down = QPushButton("▼"); self.btn_down.setFixedWidth(30)

        layer_btns.addWidget(self.btn_new, stretch=1)
        layer_btns.addWidget(self.btn_del)
        layer_btns.addStretch()
        layer_btns.addWidget(self.btn_up)
        layer_btns.addWidget(self.btn_down)
        mid_layout.addLayout(layer_btns)
        layout.addWidget(self.mid_container, stretch=1)

        # 3. BAWAH: TOMBOL ADD CONTENT
        content_btn_layout = QHBoxLayout()
        content_btn_layout.setSpacing(2)
        self.btn_add_content = QPushButton("+ Video/Img")
        self.btn_add_content.setFixedHeight(35)
        self.btn_add_content.setEnabled(False) 
        self.btn_add_text = QPushButton("+ Teks")
        self.btn_add_text.setFixedHeight(35)
        self.btn_add_text.setEnabled(False)
        self.btn_add_paragraph = QPushButton("+ Para")
        self.btn_add_paragraph.setFixedHeight(35)
        self.btn_add_paragraph.setEnabled(False)

        content_btn_layout.addWidget(self.btn_add_content, stretch=6)
        content_btn_layout.addWidget(self.btn_add_text, stretch=2)
        content_btn_layout.addWidget(self.btn_add_paragraph, stretch=2)
        layout.addLayout(content_btn_layout)

        # 4. EXTRA & RENDER
        self.render_tab = RenderTab()
        layout.addWidget(self.render_tab)

        # Koneksi Signal BG
        self.spin_bg_x.valueChanged.connect(self._emit_bg_change)
        self.spin_bg_y.valueChanged.connect(self._emit_bg_change)
        self.spin_bg_scale.valueChanged.connect(self._emit_bg_change)
        self.spn_blur.valueChanged.connect(self._emit_bg_change)
        self.spn_vignette.valueChanged.connect(self._emit_bg_change)
    
    def _create_spinbox(self, tooltip, min_v, max_v, default=0):
        sb = QSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(default)
        sb.setToolTip(tooltip)
        sb.setButtonSymbols(QSpinBox.NoButtons) 
        sb.setStyleSheet("background-color: #444; color: white; padding: 2px;")
        return sb

    def _emit_bg_change(self):
        data = {
            "x": self.spin_bg_x.value(),
            "y": self.spin_bg_y.value(),
            "scale": self.spin_bg_scale.value(),
            "blur": self.spn_blur.value(),
            "vig": self.spn_vignette.value(),
            "lock": self.chk_bg_lock.isChecked() # ✅ BARU: Kirim status lock
        }
        self.sig_bg_changed.emit(data)
        
    def _on_bg_lock_toggled(self, checked):
        """Handler saat tombol Lock diklik"""
        # Ubah warna icon gembok
        if checked:
            self.chk_bg_lock.setStyleSheet("font-weight: bold; color: #ff7675;") 
        else:
            self.chk_bg_lock.setStyleSheet("font-weight: bold; color: #dfe6e9;") 
            
        # 1. Update tampilan UI (Enable/Disable spinbox)
        self.show_bg_controls(visible=True)
        
        # 2. ✅ PENTING: Picu sinyal agar BackgroundItem tau dia dikunci
        self._emit_bg_change()
        
    def _on_bg_toggled_internal(self, checked):
        self.btn_add_bg.setEnabled(checked)
        self.btn_add_bg.setStyleSheet("background-color: #2d3436; color: white;" if checked else "background-color: #636e72; color: #b2bec3;")
        
        self.chk_bg_toggle.setText("ON" if checked else "OFF")
        
        # Panggil fungsi sentral untuk atur enable/disable widget
        self.show_bg_controls(visible=True)
        
        self.sig_bg_toggle.emit(checked)
        
    def show_bg_controls(self, visible=True):
        """
        Mengatur status Enable/Disable input background.
        Logika:
        1. Jika Toggle OFF -> Semua Mati.
        2. Jika Toggle ON & Lock ON -> Transform Mati, Efek Hidup.
        3. Jika Toggle ON & Lock OFF -> Semua Hidup.
        """
        is_bg_on = self.chk_bg_toggle.isChecked()
        is_locked = self.chk_bg_lock.isChecked()
        
        # Tombol Lock hanya aktif jika BG menyala
        self.chk_bg_lock.setEnabled(is_bg_on)

        # 1. Kontrol Transform (X, Y, Scale)
        # Syarat: Panel Visible + BG Nyala + TIDAK dikunci
        can_transform = visible and is_bg_on and not is_locked
        self.spin_bg_x.setEnabled(can_transform)
        self.spin_bg_y.setEnabled(can_transform)
        self.spin_bg_scale.setEnabled(can_transform)
            
        # 2. Kontrol Efek (Blur, Vignette)
        # Syarat: Panel Visible + BG Nyala (Lock tidak berpengaruh)
        can_edit_effect = visible and is_bg_on
        self.spn_vignette.setEnabled(can_edit_effect)
        self.spn_blur.setEnabled(can_edit_effect)
            
    def set_bg_values(self, data):
        self.blockSignals(True)
        self.spin_bg_x.setValue(data.get("x", 0))
        self.spin_bg_y.setValue(data.get("y", 0))
        self.spin_bg_scale.setValue(data.get("scale", 100))
        self.spn_blur.setValue(data.get("blur", 0))
        self.spn_vignette.setValue(data.get("vig", 0))
        self.blockSignals(False)
  
    def set_content_button_enabled(self, enabled):
        self.btn_add_content.setEnabled(enabled)
        self.btn_add_text.setEnabled(enabled)
        self.btn_add_paragraph.setEnabled(enabled)

        if enabled:
            self.btn_add_content.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold;")
            self.btn_add_text.setStyleSheet("background-color: #00b894; color: white; font-weight: bold;") 
            self.btn_add_paragraph.setStyleSheet("background-color: #0984e3; color: white; font-weight: bold;") 
        else:
            disabled_style = "background-color: #504945; color: #a89984; font-weight: bold;"
            self.btn_add_content.setStyleSheet(disabled_style)
            self.btn_add_text.setStyleSheet(disabled_style)
            self.btn_add_paragraph.setStyleSheet(disabled_style)
               
    def _connect_internal_signals(self):
        self.btn_up.clicked.connect(self.action_move_up)
        self.btn_down.clicked.connect(self.action_move_down)
        self.btn_del.clicked.connect(self.action_delete)
        self.list_layers.itemClicked.connect(self._on_list_item_clicked)

    def set_delete_enabled(self, enabled):
        self.btn_del.setEnabled(enabled)
            
    def set_reorder_enabled(self, enabled):
        self.btn_up.setEnabled(enabled)
        self.btn_down.setEnabled(enabled)

    def action_add_new(self, shape="portrait"):
        count = self.list_layers.count()
        if count < 26: frame_char = chr(65 + count)
        else: frame_char = f"Z{count}"
        
        # Kirim sinyal saja, biarkan Controller yang handle add_layer_item_custom
        self.sig_layer_created.emit(frame_char, shape)
    
    # --- METODE BARU UNTUK MENAMBAH ITEM KE LIST SECARA MANUAL ---
    def add_layer_item_custom(self, full_name):
        """Menambahkan item ke ListWidget dengan nama kustom (misal: FRAME TEXT 1)"""
        item = QListWidgetItem(full_name)
        self.list_layers.addItem(item)
        self.list_layers.setCurrentItem(item)
        # Scroll ke bawah
        self.list_layers.scrollToItem(item)

    def action_move_up(self):
        row = self.list_layers.currentRow()
        if row > 0:
            item = self.list_layers.takeItem(row)
            self.list_layers.insertItem(row - 1, item)
            self.list_layers.setCurrentRow(row - 1)
            self.sig_layer_reordered.emit(row, row - 1)

    def action_move_down(self):
        row = self.list_layers.currentRow()
        if row < self.list_layers.count() - 1:
            item = self.list_layers.takeItem(row)
            self.list_layers.insertItem(row + 1, item)
            self.list_layers.setCurrentRow(row + 1)
            self.sig_layer_reordered.emit(row, row + 1)
            
    def action_delete(self):
        row = self.list_layers.currentRow()
        if row >= 0:
            item = self.list_layers.takeItem(row)
            txt = item.text()
            if "FRAME " in txt:
                code = txt.replace("FRAME ", "")
                self.sig_delete_layer.emit(code)

    def _on_list_item_clicked(self, item):
        txt = item.text() 
        if "FRAME " in txt:
            code = txt.replace("FRAME ", "")
            self.sig_layer_selected.emit(code)

    def select_layer_by_code(self, code):
        target_name = f"FRAME {code}"
        for i in range(self.list_layers.count()):
            item = self.list_layers.item(i)
            # Match persis
            if item.text() == target_name:
                self.list_layers.setCurrentItem(item)
                self.list_layers.scrollToItem(item)
                break