# gui/right_panel/caption_tab.py
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                             QLabel, QSpinBox, QPushButton, QComboBox, 
                             QScrollArea, QCheckBox, QHBoxLayout, 
                             QFontComboBox, QLineEdit, QColorDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class CaptionTab(QScrollArea):
    sig_style_changed = Signal(dict)
    sig_enable_toggled = Signal(bool)
    sig_generate_caption = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        
        # Default State
        self.text_color_hex = "#ffffff"
        self.stroke_color_hex = "#000000"
        self.bg_color_hex = "#000000"

        container = QWidget()
        container.setStyleSheet("background-color: #23272e;")
        self.main_layout = QVBoxLayout(container)

        # --- 1. MASTER TOGGLE ---
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
        self._init_api_section()

        self.main_layout.addWidget(self.content_wrapper)
        self.main_layout.addStretch()
        self.setWidget(container)

        # State Awal
        self.content_wrapper.setEnabled(False)
        self.chk_enable_caption.toggled.connect(self._on_master_toggle)
        self._connect_signals()

    def _init_template_section(self):
        group = QGroupBox("10 CAPTION TEMPLATES")
        group.setStyleSheet("QGroupBox { color: #61afef; font-weight: bold; }")
        grid = QGridLayout(group)
        
        templates = [
            {"name": "1. Basic", "text": "#ffffff", "font_weight": "Normal", "stroke_on": False, "bg_on": False},
            {"name": "2. Bold Outline", "text": "#ffffff", "font_weight": "Bold", "stroke_on": True, "stroke_w": 4, "stroke_c": "#000000"},
            {"name": "3. Bold Shadow", "text": "#ffffff", "font_weight": "Bold", "shadow_on": True, "stroke_on": False},
            {"name": "4. Highlight", "text": "#ffffff", "font_weight": "Bold", "highlight_c": "#ffcc00", "stroke_on": True, "stroke_w": 1},
            {"name": "5. Boxed", "text": "#ffffff", "font_weight": "Normal", "bg_on": True, "bg_c": "#000000", "bg_opacity": 180},
            {"name": "6. Rounded Box", "text": "#ffffff", "font_weight": "Normal", "bg_on": True, "bg_c": "#000000", "bg_opacity": 180, "bg_rounded": 15},
            {"name": "7. Karaoke", "text": "#ffffff", "karaoke_on": True, "highlight_c": "#ff00ff", "stroke_on": True},
            {"name": "8. Cinematic", "text": "#e0e0e0", "font_weight": "Light", "letter_spacing": 5, "stroke_on": False},
            {"name": "9. Minimal", "text": "#ffffff", "font_family": "Segoe UI", "stroke_on": False, "bg_on": False},
            {"name": "10. Pop", "text": "#00ff00", "font_weight": "Black", "stroke_on": True, "stroke_w": 2, "stroke_c": "#000000"}
        ]

        for i, t in enumerate(templates):
            btn = QPushButton(t["name"])
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("background-color: #3e4451; color: white; padding: 5px; border-radius: 4px;")
            # PENTING: Gunakan default argumen pada lambda agar nilai 't' terkunci dengan benar
            btn.clicked.connect(lambda checked=False, temp=t: self.apply_visual_template(temp))
            grid.addWidget(btn, i // 2, i % 2)
        
        self.layout.addWidget(group)

    def apply_visual_template(self, t):
        self.text_color_hex = t.get("text", "#ffffff")
        if "stroke_c" in t: self.stroke_color_hex = t["stroke_c"]
        if "bg_c" in t: self.bg_color_hex = t["bg_c"]

        self.chk_stroke.setChecked(t.get("stroke_on", False))
        self.spn_stroke.setValue(t.get("stroke_w", 2))
        self.chk_bg.setChecked(t.get("bg_on", False))
        
        # Kirim template dict sebagai extra_props
        self._emit_style_update(extra_props=t)

    def _init_styling_section(self):
        group = QGroupBox("PROPERTIES")
        group.setStyleSheet("QGroupBox { color: #c678dd; font-weight: bold; }")
        grid = QGridLayout(group)

        self.font_combo = QFontComboBox()
        self.spn_size = QSpinBox()
        self.spn_size.setRange(10, 500); self.spn_size.setValue(45)

        self.btn_text_color = QPushButton("Color")
        self.btn_text_color.setStyleSheet(f"background-color: {self.text_color_hex}")
        self.btn_text_color.clicked.connect(lambda: self._pick_color("text"))

        self.chk_stroke = QCheckBox("Stroke")
        self.spn_stroke = QSpinBox()
        self.btn_stroke_color = QPushButton("Str Color")
        self.btn_stroke_color.setStyleSheet(f"background-color: {self.stroke_color_hex}")
        self.btn_stroke_color.clicked.connect(lambda: self._pick_color("stroke"))

        self.chk_bg = QCheckBox("Bg Box")
        self.btn_bg_color = QPushButton("Bg Color")
        self.btn_bg_color.setStyleSheet(f"background-color: {self.bg_color_hex}")
        self.btn_bg_color.clicked.connect(lambda: self._pick_color("bg"))

        grid.addWidget(QLabel("Font:"), 0, 0); grid.addWidget(self.font_combo, 0, 1, 1, 3)
        grid.addWidget(QLabel("Size:"), 1, 0); grid.addWidget(self.spn_size, 1, 1)
        grid.addWidget(self.btn_text_color, 1, 2, 1, 2)
        grid.addWidget(self.chk_stroke, 2, 0); grid.addWidget(self.spn_stroke, 2, 1)
        grid.addWidget(self.btn_stroke_color, 2, 2, 1, 2)
        grid.addWidget(self.chk_bg, 3, 0); grid.addWidget(self.btn_bg_color, 3, 1, 1, 3)

        self.layout.addWidget(group)

    def _init_api_section(self):
        group = QGroupBox("GENERATE")
        layout = QVBoxLayout(group)
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setPlaceholderText("API Key...")
        self.btn_generate = QPushButton("🚀 GENERATE CAPTION")
        self.btn_generate.clicked.connect(lambda: self.sig_generate_caption.emit({"api_key": self.txt_api_key.text()}))
        layout.addWidget(self.txt_api_key)
        layout.addWidget(self.btn_generate)
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
        # FIX: Gunakan lambda untuk membuang argumen default signal (bool/int)
        # Agar tidak masuk ke parameter 'extra_props'
        self.font_combo.currentFontChanged.connect(lambda f: self._emit_style_update())
        self.spn_size.valueChanged.connect(lambda v: self._emit_style_update())
        self.chk_stroke.toggled.connect(lambda c: self._emit_style_update())
        self.spn_stroke.valueChanged.connect(lambda v: self._emit_style_update())
        self.chk_bg.toggled.connect(lambda c: self._emit_style_update())

    def _emit_style_update(self, extra_props=None):
        data = {
            "font": self.font_combo.currentFont().family(),
            "font_size": self.spn_size.value(),
            "text_color": self.text_color_hex,
            "stroke_on": self.chk_stroke.isChecked(),
            "stroke_width": self.spn_stroke.value(),
            "stroke_color": self.stroke_color_hex,
            "bg_on": self.chk_bg.isChecked(),
            "bg_color": self.bg_color_hex
        }
        
        # Cek apakah extra_props valid dictionary
        if isinstance(extra_props, dict):
            data.update(extra_props)
            
        self.sig_style_changed.emit(data)