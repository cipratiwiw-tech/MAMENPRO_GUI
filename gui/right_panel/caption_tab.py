# FILE: gui/right_panel/caption_tab.py

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                             QLabel, QSpinBox, QPushButton, QComboBox, 
                             QScrollArea, QCheckBox, QHBoxLayout, 
                             QFontComboBox, QLineEdit, QColorDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

# --- DAFTAR PRESET (SAMA SEPERTI SEBELUMNYA) ---
CAPTION_PRESETS = [
    {"name": "1. CLEAN PRO (Standard)", "settings": {"font_size": 42, "text_color": "#FFFFFF", "stroke_on": True, "stroke_width": 2, "stroke_color": "#000000", "shadow_on": True, "shadow_strength": 1, "bg_on": False, "alignment": "bottom_center", "margin_v": 40}},
    {"name": "2. HIGH CONTRAST (Outdoor)", "settings": {"font_size": 44, "text_color": "#FFFF00", "stroke_on": True, "stroke_width": 3, "stroke_color": "#000000", "shadow_on": False, "bg_on": False, "alignment": "bottom_center", "margin_v": 45}},
    {"name": "3. DARK MODE BOX (Netflix)", "settings": {"font_size": 40, "text_color": "#FFFFFF", "stroke_on": False, "shadow_on": False, "bg_on": True, "bg_color": "#000000", "bg_opacity": 180, "alignment": "bottom_center", "margin_v": 40}},
    {"name": "4. SOFT CINEMA", "settings": {"font_size": 38, "text_color": "#E0E0E0", "stroke_on": True, "stroke_width": 1, "stroke_color": "#000000", "shadow_on": True, "shadow_strength": 2, "bg_on": False, "alignment": "bottom_center", "margin_v": 60}},
    {"name": "5. STROKE HEAVY (Gaming)", "settings": {"font_size": 46, "text_color": "#FFFFFF", "stroke_on": True, "stroke_width": 4, "stroke_color": "#000000", "shadow_on": True, "bg_on": False, "alignment": "bottom_center", "margin_v": 40}},
    {"name": "6. MODERN FLAT BOX", "settings": {"font_size": 40, "text_color": "#FFFFFF", "stroke_on": False, "shadow_on": False, "bg_on": True, "bg_color": "#333333", "bg_opacity": 150, "alignment": "bottom_center", "margin_v": 50}},
    {"name": "7. SOCIAL POP (Big)", "settings": {"font_size": 52, "text_color": "#FFFFFF", "stroke_on": True, "stroke_width": 3, "stroke_color": "#000000", "shadow_on": True, "bg_on": False, "alignment": "middle_lower", "margin_v": 120}},
    {"name": "8. KARAOKE LIGHT", "settings": {"font_size": 42, "text_color": "#FFFFFF", "highlight_color": "#00FFFF", "stroke_on": True, "stroke_width": 2, "stroke_color": "#000000", "shadow_on": False, "bg_on": False, "karaoke_mode": True, "alignment": "bottom_center", "margin_v": 40}},
    {"name": "9. NEWS LOWER 3RD", "settings": {"font_size": 36, "text_color": "#FFFFFF", "stroke_on": False, "shadow_on": False, "bg_on": True, "bg_color": "#001f3f", "bg_opacity": 220, "alignment": "bottom_center", "margin_v": 40}},
    {"name": "10. MINIMAL WHITE BOX", "settings": {"font_size": 38, "text_color": "#000000", "stroke_on": False, "shadow_on": False, "bg_on": True, "bg_color": "#FFFFFF", "bg_opacity": 215, "alignment": "bottom_center", "margin_v": 40}}
]

class CaptionTab(QScrollArea):
    sig_style_changed = Signal(dict)
    sig_enable_toggled = Signal(bool)
    sig_generate_caption = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        
        self.text_color_hex = "#ffffff"
        self.stroke_color_hex = "#000000"
        self.bg_color_hex = "#000000"

        container = QWidget()
        container.setStyleSheet("background-color: #23272e;")
        self.main_layout = QVBoxLayout(container)

        self.chk_enable_caption = QCheckBox("✅ ENABLE CAPTION LAYER")
        self.chk_enable_caption.setStyleSheet("""
            QCheckBox { font-weight: bold; color: #abb2bf; font-size: 14px; padding: 10px; border: 1px solid #3e4451; border-radius: 5px;}
            QCheckBox::checked { color: #98c379; border: 1px solid #98c379; }
        """)
        self.main_layout.addWidget(self.chk_enable_caption)

        self.content_wrapper = QWidget()
        self.layout = QVBoxLayout(self.content_wrapper)
        self.layout.setContentsMargins(0,0,0,0)

        self._init_template_section()
        self._init_styling_section()
        self._init_word_limit_section() # Ubah nama section

        self.main_layout.addWidget(self.content_wrapper)
        self.main_layout.addStretch()
        self.setWidget(container)

        self.content_wrapper.setEnabled(False)
        self.chk_enable_caption.toggled.connect(self._on_master_toggle)
        self._connect_signals()

    def _init_template_section(self):
        group = QGroupBox("STYLE PRESETS")
        group.setStyleSheet("QGroupBox { color: #61afef; font-weight: bold; }")
        grid = QGridLayout(group)
        for i, t in enumerate(CAPTION_PRESETS):
            btn = QPushButton(t["name"])
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("QPushButton { background-color: #3e4451; color: white; padding: 6px; border-radius: 4px; text-align: left;} QPushButton:hover { background-color: #4b5263; }")
            btn.clicked.connect(lambda checked=False, s=t["settings"]: self.apply_visual_template(s))
            grid.addWidget(btn, i // 2, i % 2)
        self.layout.addWidget(group)

    def apply_visual_template(self, s):
        if "text_color" in s: 
            self.text_color_hex = s["text_color"]
            self.btn_text_color.setStyleSheet(f"background-color: {self.text_color_hex}")
        if "stroke_color" in s: 
            self.stroke_color_hex = s["stroke_color"]
            self.btn_stroke_color.setStyleSheet(f"background-color: {self.stroke_color_hex}")
        if "bg_color" in s: 
            self.bg_color_hex = s["bg_color"]
            self.btn_bg_color.setStyleSheet(f"background-color: {self.bg_color_hex}")
        if "stroke_on" in s: self.chk_stroke.setChecked(s["stroke_on"])
        if "stroke_width" in s: self.spn_stroke.setValue(s["stroke_width"])
        if "bg_on" in s: self.chk_bg.setChecked(s["bg_on"])
        if "font_size" in s: self.spn_size.setValue(s["font_size"])
        self._emit_style_update(extra_props=s)

    def _init_styling_section(self):
        group = QGroupBox("VISUAL PROPERTIES")
        group.setStyleSheet("QGroupBox { color: #c678dd; font-weight: bold; }")
        grid = QGridLayout(group)
        self.font_combo = QFontComboBox()
        self.spn_size = QSpinBox(); self.spn_size.setRange(10, 500); self.spn_size.setValue(42)
        self.btn_text_color = QPushButton("Color"); self.btn_text_color.clicked.connect(lambda: self._pick_color("text"))
        self.chk_stroke = QCheckBox("Stroke"); self.spn_stroke = QSpinBox()
        self.btn_stroke_color = QPushButton("Str Color"); self.btn_stroke_color.clicked.connect(lambda: self._pick_color("stroke"))
        self.chk_bg = QCheckBox("Bg Box"); self.btn_bg_color = QPushButton("Bg Color"); self.btn_bg_color.clicked.connect(lambda: self._pick_color("bg"))

        grid.addWidget(QLabel("Font:"), 0, 0); grid.addWidget(self.font_combo, 0, 1, 1, 3)
        grid.addWidget(QLabel("Size:"), 1, 0); grid.addWidget(self.spn_size, 1, 1)
        grid.addWidget(self.btn_text_color, 1, 2, 1, 2)
        grid.addWidget(self.chk_stroke, 2, 0); grid.addWidget(self.spn_stroke, 2, 1)
        grid.addWidget(self.btn_stroke_color, 2, 2, 1, 2)
        grid.addWidget(self.chk_bg, 3, 0); grid.addWidget(self.btn_bg_color, 3, 1, 1, 3)
        self.layout.addWidget(group)

    # [MODIFIKASI] Hanya sisakan Word Count
    def _init_word_limit_section(self):
        group = QGroupBox("WORD LIMIT PER LINE")
        group.setStyleSheet("QGroupBox { color: #e5c07b; font-weight: bold; }")
        layout = QHBoxLayout(group)

        self.lbl_words = QLabel("Max Words:")
        self.spn_words = QSpinBox()
        self.spn_words.setRange(1, 10) # 1 sampai 10 kata
        self.spn_words.setValue(3)     # Default 3 kata
        
        # Connect signal saat value berubah agar update preview
        self.spn_words.valueChanged.connect(lambda: self._emit_style_update())

        layout.addWidget(self.lbl_words)
        layout.addWidget(self.spn_words)
        self.layout.addWidget(group)

    def _on_master_toggle(self, checked):
        self.content_wrapper.setEnabled(checked)
        self.sig_enable_toggled.emit(checked)

    def _pick_color(self, target):
        c = QColorDialog.getColor()
        if c.isValid():
            hex_c = c.name()
            if target == "text": 
                self.text_color_hex = hex_c
                self.btn_text_color.setStyleSheet(f"background-color: {hex_c}")
            elif target == "stroke": 
                self.stroke_color_hex = hex_c
                self.btn_stroke_color.setStyleSheet(f"background-color: {hex_c}")
            elif target == "bg": 
                self.bg_color_hex = hex_c
                self.btn_bg_color.setStyleSheet(f"background-color: {hex_c}")
            self._emit_style_update()

    def _connect_signals(self):
        self.font_combo.currentFontChanged.connect(lambda f: self._emit_style_update())
        self.spn_size.valueChanged.connect(lambda v: self._emit_style_update())
        self.chk_stroke.toggled.connect(lambda c: self._emit_style_update())
        self.spn_stroke.valueChanged.connect(lambda v: self._emit_style_update())
        self.chk_bg.toggled.connect(lambda c: self._emit_style_update())

    # [LOGIKA DUMMY TEXT OTOMATIS]
    def _emit_style_update(self, extra_props=None):
        config = self.get_caption_config()
        
        # Update dummy text berdasarkan Max Words
        max_words = config["max_words"]
        dummy_pool = ["LOREM", "IPSUM", "DOLOR", "SIT", "AMET", "CONSECTETUR", "ADIPISCING", "ELIT"]
        
        # Ambil sejumlah kata sesuai settingan
        # Kalau setting 3 -> LOREM IPSUM DOLOR
        # Kalau setting 2 -> LOREM IPSUM
        selected_words = []
        for i in range(max_words):
            selected_words.append(dummy_pool[i % len(dummy_pool)])
            
        dummy_text = " ".join(selected_words)
        
        # Masukkan ke config agar Controller bisa update VideoItem
        config["text_content"] = dummy_text
        
        if isinstance(extra_props, dict):
            config.update(extra_props)
            
        self.sig_style_changed.emit(config)

    def get_caption_config(self):
        return {
            "font": self.font_combo.currentFont().family(),
            "font_size": self.spn_size.value(),
            "text_color": self.text_color_hex,
            "stroke_on": self.chk_stroke.isChecked(),
            "stroke_width": self.spn_stroke.value(),
            "stroke_color": self.stroke_color_hex,
            "bg_on": self.chk_bg.isChecked(),
            "bg_color": self.bg_color_hex,
            
            # [SETTING LOGIC]
            "max_words": self.spn_words.value(),
            "min_silence": 0.5, # HARDCODED DEFAULT (Otomatis deteksi jeda 0.5s)
            "split_mode": "Hybrid" # Mode khusus untuk backend
        }