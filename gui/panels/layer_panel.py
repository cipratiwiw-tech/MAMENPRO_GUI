from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QGridLayout, QLabel, QPushButton, QCheckBox, 
                             QSpinBox, QListWidget, QFrame, QScrollArea, QComboBox, 
                             # Tambahkan QToolButton di sini
                             QTabWidget, QListWidgetItem, QMenu, QAbstractSpinBox, QDoubleSpinBox, QToolButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
import math

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
        
        # [UPGRADE] Lebar panel
        self.setFixedWidth(300) 
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # [STYLE] Compact Input Style (Shared)
        self.spinbox_style = """
            QSpinBox {
                background-color: #2b2b2b;
                color: #dcdcdc;
                border: 1px solid #3e4451;
                border-radius: 2px;
                padding-left: 0px;  
                padding-right: 4px; 
                margin: 0px;
            }
            QSpinBox:focus {
                border: 1px solid #56b6c2;
                background-color: #1e1e1e;
            }
            QDoubleSpinBox {
                background-color: #2b2b2b;
                color: #dcdcdc;
                border: 1px solid #3e4451;
                border-radius: 2px;
                padding-left: 0px;  
                padding-right: 4px; 
                margin: 0px;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #56b6c2;
                background-color: #1e1e1e;
            }
        """
        
        # --- SISTEM TAB ---
        self.tabs = QTabWidget()
        # Styling Tabs
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3e4451; background: #23272e; }
            QTabBar::tab { background: #2d3436; color: #abb2bf; padding: 6px 10px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #23272e; color: #61afef; font-weight: bold; border-top: 2px solid #61afef; }
            QTabBar::tab:hover { background: #3e4451; }
        """)
        
        self.main_layout.addWidget(self.tabs)
        
        # 1. Tab Editor
        self.tab_editor = QWidget()
        self._init_editor_ui()
        
        self.tab_templates = TemplateTab()
        self.tab_chroma = PresetChromaPanel()
        self.tab_audio = AudioTab()
        
        self.tabs.addTab(self.tab_editor, "Editor")
        self.tabs.addTab(self.tab_templates, "Tmpl") # Singkat agar muat
        self.tabs.addTab(self.tab_chroma, "Chroma")
        self.tabs.addTab(self.tab_audio, "Audio")

        self._connect_internal_signals()

    # --- HELPER FUNCTIONS (Unified Compact Logic) ---
    def _create_label(self, text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet("color: #abb2bf; font-size: 11px; margin-right: 4px;") 
        return lbl

    def _optimize_width(self, sb, min_val, max_val, suffix):
        s_min = f"{min_val}{suffix}"
        s_max = f"{max_val}{suffix}"
        longest_text = s_max if len(s_max) > len(s_min) else s_min
        fm = sb.fontMetrics()
        text_width = fm.horizontalAdvance(longest_text)
        final_width = max(45, text_width + 24)
        sb.setFixedWidth(final_width)

    def _style_spinbox(self, sb, min_v, max_v, suffix):
        sb.setButtonSymbols(QAbstractSpinBox.NoButtons) 
        sb.setAlignment(Qt.AlignRight) 
        sb.setStyleSheet(self.spinbox_style)
        self._optimize_width(sb, min_v, max_v, suffix)

    def _create_spinbox(self, tooltip, min_v, max_v, val, suffix=""):
        sb = QSpinBox()
        sb.setRange(min_v, max_v); sb.setValue(val); sb.setSuffix(suffix)
        sb.setToolTip(tooltip)
        self._style_spinbox(sb, min_v, max_v, suffix)
        return sb

    def _create_double_spinbox(self, tooltip, min_v, max_v, val, suffix="", step=0.05):
        """Helper baru untuk input float"""
        sb = QDoubleSpinBox()
        sb.setRange(min_v, max_v); sb.setValue(val); sb.setSuffix(suffix)
        sb.setSingleStep(step)
        sb.setToolTip(tooltip)
        sb.setDecimals(2)
        self._style_spinbox(sb, min_v, max_v, suffix)
        return sb
    # Letakkan ini di bawah method _create_double_spinbox
    def _create_reset_btn(self, tooltip):
        btn = QToolButton()
        btn.setText("↺") # Ikon panah memutar
        btn.setToolTip(tooltip)
        btn.setFixedSize(20, 20)
        btn.setCursor(Qt.PointingHandCursor)
        # Style agar transparan dan rapi
        btn.setStyleSheet("""
            QToolButton { border: none; background: transparent; color: #5c6370; font-weight: bold; }
            QToolButton:hover { color: #61afef; }
        """)
        return btn
    
    # --- UI INIT (FINAL LAYOUT) ---
    def _init_editor_ui(self):
        layout = QVBoxLayout(self.tab_editor)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # --- AUDIO MIXER (Tetap) ---
        self.group_audio = QGroupBox("AUDIO MIXER")
        self.group_audio.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #c678dd; margin-top: 6px; color: #c678dd; }")
        
        audio_grid = QGridLayout(self.group_audio)
        audio_grid.setContentsMargins(5, 10, 5, 5)
        audio_grid.setSpacing(8)

        self.btn_add_audio = QPushButton("Add Music")
        self.btn_add_audio.setCursor(Qt.PointingHandCursor)
        self.btn_add_audio.setStyleSheet("background-color: #3e4451; color: #dcdcdc; border-radius: 2px; padding: 3px;")
        
        self.chk_mute = QCheckBox("Mute")
        self.chk_mute.setStyleSheet("color: #abb2bf;")
        
        self.spn_volume = self._create_spinbox("Volume", 0, 200, 100, "%")
        
        audio_grid.addWidget(self.btn_add_audio, 0, 0)
        audio_grid.addWidget(self.chk_mute, 0, 1)
        audio_grid.addWidget(self._create_label("Vol:"), 0, 2)
        audio_grid.addWidget(self.spn_volume, 0, 3)
        layout.addWidget(self.group_audio)

        # --- BACKGROUND GROUP ---
        self.group_bg = QGroupBox("BACKGROUND")
        self.group_bg.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #56b6c2; margin-top: 6px; color: #56b6c2; }")
        bg_main_layout = QVBoxLayout(self.group_bg)
        bg_main_layout.setSpacing(8)
        
        # 0. HEADER: [BG ON/OFF] | [Replace] | [Lock]
        row_header = QHBoxLayout()
        
        # Tombol Utama ON/OFF Background
        self.chk_bg_toggle = QCheckBox("BG")
        self.chk_bg_toggle.setToolTip("Show/Hide Background Layer")
        self.chk_bg_toggle.setChecked(True)
        self.chk_bg_toggle.setStyleSheet("font-weight: bold; color: #98c379;")
        self.chk_bg_toggle.toggled.connect(self._on_bg_toggled_internal)

        self.btn_add_bg = QPushButton("Replace")
        self.btn_add_bg.setStyleSheet("background-color: #3e4451; color: white; border-radius: 2px;")
        
        self.chk_bg_lock = QPushButton("🔓")
        self.chk_bg_lock.setCheckable(True)
        self.chk_bg_lock.setFixedWidth(30)
        self.chk_bg_lock.setToolTip("Lock Position")
        self.chk_bg_lock.setStyleSheet("background-color: #2b2b2b; border: 1px solid #3e4451;")

        row_header.addWidget(self.chk_bg_toggle)
        row_header.addWidget(self.btn_add_bg)
        row_header.addWidget(self.chk_bg_lock)
        bg_main_layout.addLayout(row_header)

        # 1. BARIS PERTAMA: X, Y, Scale
        row_one = QHBoxLayout()
        row_one.setSpacing(2)
        
        self.spin_bg_x = self._create_spinbox("Pos X", -3000, 3000, 0, "")
        self.spin_bg_y = self._create_spinbox("Pos Y", -3000, 3000, 0, "")
        self.spin_bg_scale = self._create_spinbox("Scale", 1, 1000, 100, "%")
        
        for w in [self.spin_bg_x, self.spin_bg_y, self.spin_bg_scale]: w.setFixedWidth(45) 

        row_one.addWidget(self._create_label("X:"))
        row_one.addWidget(self.spin_bg_x)
        row_one.addWidget(self._create_label("Y:"))
        row_one.addWidget(self.spin_bg_y)
        row_one.addWidget(self._create_label("Zm:"))
        row_one.addWidget(self.spin_bg_scale)
        bg_main_layout.addLayout(row_one)
        
        # 2. BARIS KEDUA: Vig Str, Rad, Ang
        row_two = QHBoxLayout()
        row_two.setSpacing(2)
        
        self.spn_vig_strength = self._create_double_spinbox("Str", 0.0, 1.0, 0.60)
        self.spn_vig_radius = self._create_double_spinbox("Rad", 0.2, 1.2, 0.70)
        self.spn_vig_angle = self._create_double_spinbox("Ang", -180.0, 180.0, -10.0, "°", step=10.0)
        self.spn_vig_angle.setWrapping(True)

        for w in [self.spn_vig_strength, self.spn_vig_radius, self.spn_vig_angle]: w.setFixedWidth(45)

        row_two.addWidget(self._create_label("V.Str:"))
        row_two.addWidget(self.spn_vig_strength)
        row_two.addWidget(self._create_label("Rad:"))
        row_two.addWidget(self.spn_vig_radius)
        row_two.addWidget(self._create_label("Ang:"))
        row_two.addWidget(self.spn_vig_angle)
        bg_main_layout.addLayout(row_two)

        # 3. BARIS KETIGA: Blur | Reset Blur | Reset Vig | [Fx ON/OFF]
        row_three = QHBoxLayout()
        row_three.setSpacing(4)
        
        self.spn_blur = self._create_spinbox("Blur", 0, 100, 12)
        self.spn_blur.setFixedWidth(45)
        
        self.btn_rst_blur = self._create_reset_btn("Reset Blur (0)")
        self.btn_rst_blur.clicked.connect(lambda: self.spn_blur.setValue(12))
        
        self.btn_rst_vig = self._create_reset_btn("Reset Vignette (Default)")
        self.btn_rst_vig.clicked.connect(self._reset_vignette_values)
        
        # [NEW] Tombol ON/OFF Khusus Efek
        self.chk_effect_toggle = QCheckBox("Fx")
        self.chk_effect_toggle.setToolTip("Enable/Disable Blur & Vignette Effects")
        self.chk_effect_toggle.setChecked(True)
        self.chk_effect_toggle.setStyleSheet("font-weight: bold; color: #61afef; margin-left: 4px;")
        self.chk_effect_toggle.toggled.connect(self._on_effect_toggled)

        row_three.addWidget(self._create_label("Blur:"))
        row_three.addWidget(self.spn_blur)
        row_three.addWidget(self.btn_rst_blur)
        row_three.addWidget(self.btn_rst_vig)
        row_three.addWidget(self.chk_effect_toggle) # Ditaruh di samping tombol reset
        
        bg_main_layout.addLayout(row_three)
        layout.addWidget(self.group_bg)

        # Sinyal & Koneksi
        inputs = [self.spin_bg_x, self.spin_bg_y, self.spin_bg_scale, self.spn_blur, 
                  self.spn_vig_strength, self.spn_vig_radius, self.spn_vig_angle]
        for w in inputs:
            w.valueChanged.connect(self._emit_bg_change)
        
        self.chk_bg_lock.toggled.connect(self._on_bg_lock_toggled)

        # --- TIMELINE (Tetap) ---
        self.mid_container = QGroupBox("TIMELINE")
        self.mid_container.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #e5c07b; margin-top: 6px; color: #e5c07b; }")
        mid_layout = QVBoxLayout(self.mid_container)
        mid_layout.setContentsMargins(5, 10, 5, 5)

        self.list_layers = QListWidget()
        self.list_layers.setStyleSheet("""
            QListWidget { background-color: #282c34; border: 1px solid #3e4451; color: #abb2bf; outline: none; }
            QListWidget::item { padding: 5px; border-bottom: 1px solid #2c313a; }
            QListWidget::item:selected { background-color: #3e4451; color: #61afef; border-left: 3px solid #61afef; }
            QListWidget::item:hover { background-color: #2c313a; }
        """)
        mid_layout.addWidget(self.list_layers)

        # Toolbar Timeline (Tetap)
        layer_btns = QHBoxLayout()
        layer_btns.setSpacing(2)
        
        self.btn_new = QPushButton("+ New")
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setStyleSheet("background-color: #61afef; color: #282c34; font-weight: bold; border-radius: 2px;")
        
        self.menu_new = QMenu(self)
        self.menu_new.setStyleSheet("QMenu { background-color: #2d3436; color: white; border: 1px solid #3e4451; } QMenu::item:selected { background-color: #61afef; color: black; }")
        self.menu_new.addAction("Portrait (9:16)", lambda: self.action_add_new("portrait"))
        self.menu_new.addAction("Landscape (16:9)", lambda: self.action_add_new("landscape"))
        self.menu_new.addAction("Square (1:1)", lambda: self.action_add_new("square"))
        self.menu_new.addAction("Circle", lambda: self.action_add_new("circle"))
        self.btn_new.setMenu(self.menu_new)
        
        self.btn_del = QPushButton("Del") 
        self.btn_del.setFixedWidth(40)
        self.btn_del.setStyleSheet("background-color: #e06c75; color: white; font-weight: bold; border-radius: 2px;")
        
        self.btn_up = QPushButton("▲")
        self.btn_up.setFixedWidth(25)
        self.btn_up.setStyleSheet("background-color: #3e4451; color: white; border-radius: 2px;")
        
        self.btn_down = QPushButton("▼")
        self.btn_down.setFixedWidth(25)
        self.btn_down.setStyleSheet("background-color: #3e4451; color: white; border-radius: 2px;")

        layer_btns.addWidget(self.btn_new)
        layer_btns.addWidget(self.btn_del)
        layer_btns.addWidget(self.btn_up)
        layer_btns.addWidget(self.btn_down)
        mid_layout.addLayout(layer_btns)
        
        layout.addWidget(self.mid_container, stretch=1)

        # --- TOMBOL BAWAH (Tetap) ---
        content_btn_layout = QHBoxLayout()
        content_btn_layout.setSpacing(4)
        
        self.btn_add_content = QPushButton("+ Media")
        self.btn_add_text = QPushButton("+ Text")
        self.btn_add_paragraph = QPushButton("+ Para")
        
        for btn in [self.btn_add_content, self.btn_add_text, self.btn_add_paragraph]:
            btn.setFixedHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setEnabled(False)
            btn.setStyleSheet("background-color: #2b2b2b; color: #5c6370; border: 1px solid #3e4451; border-radius: 2px;")

        content_btn_layout.addWidget(self.btn_add_content, 2)
        content_btn_layout.addWidget(self.btn_add_text, 1)
        content_btn_layout.addWidget(self.btn_add_paragraph, 1)
        layout.addLayout(content_btn_layout)

        # Extra & Render
        self.render_tab = RenderTab()
        layout.addWidget(self.render_tab)

    def _reset_vignette_values(self):
        self.spn_vig_strength.setValue(0.60)
        self.spn_vig_radius.setValue(0.70) # Default radius
        self.spn_vig_angle.setValue(-10.0)
        
    # --- LOGIC HANDLERS ---
    def _emit_bg_change(self):
        # Cek apakah Efek ON atau OFF
        fx_on = self.chk_effect_toggle.isChecked()
        
        data = {
            "x": self.spin_bg_x.value(),
            "y": self.spin_bg_y.value(),
            "scale": self.spin_bg_scale.value(),
            # Jika FX OFF, kirim 0 ke engine (tapi UI tetap angka asli)
            "blur": self.spn_blur.value() if fx_on else 0,
            "vig_strength": self.spn_vig_strength.value() if fx_on else 0.0,
            
            "vig_radius": self.spn_vig_radius.value(),
            "vig_angle": self.spn_vig_angle.value(),
            "lock": self.chk_bg_lock.isChecked()
        }
        self.sig_bg_changed.emit(data)
        
    def _on_bg_lock_toggled(self, checked):
        if checked:
            self.chk_bg_lock.setText("🔒")
            self.chk_bg_lock.setStyleSheet("background-color: #e06c75; color: white; border: none;")
        else:
            self.chk_bg_lock.setText("🔓")
            self.chk_bg_lock.setStyleSheet("background-color: #2b2b2b; color: #dcdcdc; border: 1px solid #3e4451;")
            
        self.show_bg_controls(visible=True)
        self._emit_bg_change()
        
    def _on_bg_toggled_internal(self, checked):
        self.btn_add_bg.setEnabled(checked)
        style_enabled = "background-color: #3e4451; color: white; border-radius: 2px;"
        style_disabled = "background-color: #2b2b2b; color: #5c6370; border: 1px solid #3e4451;"
        self.btn_add_bg.setStyleSheet(style_enabled if checked else style_disabled)
        
        self.chk_bg_toggle.setText("ON" if checked else "OFF")
        self.chk_bg_toggle.setStyleSheet(f"font-weight: bold; color: {'#98c379' if checked else '#e06c75'};")
        
        self.show_bg_controls(visible=True)
        self.sig_bg_toggle.emit(checked)
        
    def _on_effect_toggled(self, checked):
        # Update warna teks tombol
        if checked:
            self.chk_effect_toggle.setStyleSheet("font-weight: bold; color: #61afef; margin-left: 4px;")
        else:
            self.chk_effect_toggle.setStyleSheet("font-weight: bold; color: #5c6370; margin-left: 4px;")
            
        # Kunci/Buka input box dan kirim sinyal update
        self.show_bg_controls(visible=True)
        self._emit_bg_change()
        
    def show_bg_controls(self, visible=True):
        is_bg_on = self.chk_bg_toggle.isChecked()
        is_locked = self.chk_bg_lock.isChecked()
        is_fx_on = self.chk_effect_toggle.isChecked() # <--- Cek Fx
        
        self.chk_bg_lock.setEnabled(is_bg_on)
        self.chk_effect_toggle.setEnabled(is_bg_on)   # Fx hanya bisa diklik jika BG ON

        # Transform (Locked blocks these)
        can_transform = visible and is_bg_on and not is_locked
        self.spin_bg_x.setEnabled(can_transform)
        self.spin_bg_y.setEnabled(can_transform)
        self.spin_bg_scale.setEnabled(can_transform)
            
        # Effects (Butuh BG ON + Fx ON)
        can_edit_effect = visible and is_bg_on and is_fx_on
        self.spn_vig_strength.setEnabled(can_edit_effect)
        self.spn_vig_angle.setEnabled(can_edit_effect)
        self.spn_vig_radius.setEnabled(can_edit_effect)
        self.spn_blur.setEnabled(can_edit_effect)
        
        # Tombol reset
        self.btn_rst_blur.setEnabled(can_edit_effect)
        self.btn_rst_vig.setEnabled(can_edit_effect)
    def set_bg_values(self, data):
        """Update tampilan input box tanpa memicu sinyal balik"""
        
        # LIST WIDGET YANG HARUS DI-FREEZE SEMENTARA
        widgets = [
            self.spin_bg_x, self.spin_bg_y, self.spin_bg_scale, self.spn_blur,
            self.spn_vig_strength, self.spn_vig_radius, self.spn_vig_angle
        ]
        
        # 1. Matikan Sinyal (Block)
        for w in widgets: w.blockSignals(True)
        
        try:
            # 2. Isi Nilai Terbaru (agar sinkron dengan posisi mouse)
            if "x" in data: self.spin_bg_x.setValue(int(data["x"]))
            if "y" in data: self.spin_bg_y.setValue(int(data["y"]))
            
            if "scale" in data: self.spin_bg_scale.setValue(int(data["scale"]))
            if "blur" in data: self.spn_blur.setValue(int(data["blur"]))
            
            # Update Vignette
            if "vig_strength" in data: self.spn_vig_strength.setValue(float(data["vig_strength"]))
            if "vig_radius" in data: self.spn_vig_radius.setValue(float(data["vig_radius"]))
            if "vig_angle" in data: self.spn_vig_angle.setValue(float(data["vig_angle"]))
            
            if "lock" in data: 
                self.chk_bg_lock.setChecked(data["lock"])
                self._on_bg_lock_toggled(data["lock"])
                
        finally:
            # 3. Hidupkan Sinyal Kembali (Unblock)
            for w in widgets: w.blockSignals(False)

    def set_content_button_enabled(self, enabled):
        self.btn_add_content.setEnabled(enabled)
        self.btn_add_text.setEnabled(enabled)
        self.btn_add_paragraph.setEnabled(enabled)

        if enabled:
            self.btn_add_content.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold; border-radius: 2px;")
            self.btn_add_text.setStyleSheet("background-color: #00b894; color: white; font-weight: bold; border-radius: 2px;") 
            self.btn_add_paragraph.setStyleSheet("background-color: #0984e3; color: white; font-weight: bold; border-radius: 2px;") 
        else:
            disabled_style = "background-color: #2b2b2b; color: #5c6370; border: 1px solid #3e4451; border-radius: 2px;"
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
        self.sig_layer_created.emit(frame_char, shape)
    
    def add_layer_item_custom(self, full_name):
        item = QListWidgetItem(full_name)
        self.list_layers.addItem(item)
        self.list_layers.setCurrentItem(item)
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
            if item.text() == target_name:
                self.list_layers.setCurrentItem(item)
                self.list_layers.scrollToItem(item)
                break