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
        
        # Default Colors
        self.text_color_hex = "#ffffff"
        self.stroke_color_hex = "#000000"
        self.bg_color_hex = "#000000"

        container = QWidget()
        container.setStyleSheet("background-color: #23272e;")
        self.main_layout = QVBoxLayout(container)

        # --- 1. MASTER TOGGLE (Paling Atas) ---
        self.chk_enable_caption = QCheckBox("✅ ENABLE CAPTION LAYER")
        self.chk_enable_caption.setStyleSheet("""
            QCheckBox { font-weight: bold; color: #abb2bf; font-size: 14px; padding: 10px; border: 1px solid #3e4451; border-radius: 5px;}
            QCheckBox::checked { color: #98c379; border: 1px solid #98c379; }
        """)
        self.main_layout.addWidget(self.chk_enable_caption)

        # Wrapper Kontrol
        self.content_wrapper = QWidget()
        self.layout = QVBoxLayout(self.content_wrapper)
        self.layout.setContentsMargins(0,0,0,0)

        # Inisialisasi Sections
        self._init_template_section() # Baru: Visual Templates
        self._init_api_section()
        self._init_styling_section()

        self.main_layout.addWidget(self.content_wrapper)
        self.main_layout.addStretch()
        self.setWidget(container)

        # State Awal
        self.content_wrapper.setEnabled(False)
        self.chk_enable_caption.toggled.connect(self._on_master_toggle)
        self._connect_signals()

    def _init_template_section(self):
        group = QGroupBox("CAPTION TEMPLATES")
        group.setStyleSheet("QGroupBox { color: #61afef; font-weight: bold; }")
        
        # Menggunakan Grid agar muat 10 tombol (2 kolom)
        grid = QGridLayout(group)
        
        self.templates = [
            {"name": "1. Basic", "text": "#ffffff", "font_weight": "Normal", "stroke_on": False, "bg_on": False, "shadow_on": False},
            {"name": "2. Bold Outline", "text": "#ffffff", "font_weight": "Bold", "stroke_on": True, "stroke_w": 4, "stroke_c": "#000000", "bg_on": False},
            {"name": "3. Bold Shadow", "text": "#ffffff", "font_weight": "Bold", "shadow_on": True, "stroke_on": False, "bg_on": False},
            {"name": "4. Highlight", "text": "#ffffff", "font_weight": "Bold", "highlight_c": "#ffcc00", "stroke_on": True, "stroke_w": 1},
            {"name": "5. Boxed", "text": "#ffffff", "font_weight": "DemiBold", "bg_on": True, "bg_c": "#000000", "bg_opacity": 180, "bg_rounded": 0},
            {"name": "6. Rounded Box", "text": "#ffffff", "font_weight": "DemiBold", "bg_on": True, "bg_c": "#000000", "bg_opacity": 180, "bg_rounded": 15},
            {"name": "7. Karaoke", "text": "#ffffff", "karaoke_on": True, "highlight_c": "#ff00ff", "stroke_on": True},
            {"name": "8. Cinematic", "text": "#e0e0e0", "font_weight": "Light", "letter_spacing": 5, "stroke_on": False},
            {"name": "9. Minimal", "text": "#ffffff", "font_family": "Segoe UI", "stroke_on": False, "bg_on": False},
            {"name": "10. Pop", "text": "#00ff00", "font_weight": "Black", "stroke_on": True, "stroke_w": 2, "stroke_c": "#000000"}
        ]

        for i, t in enumerate(self.templates):
            btn = QPushButton(t["name"])
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background-color: #3e4451; color: white; padding: 8px; border-radius: 4px; text-align: left; }
                QPushButton:hover { background-color: #4b5263; border: 1px solid #61afef; }
            """)
            btn.clicked.connect(lambda checked=False, temp=t: self.apply_visual_template(temp))
            grid.addWidget(btn, i // 2, i % 2)

        self.layout.addWidget(group)

    

    def apply_visual_template(self, t):
        """Menerapkan template ke UI Controls dan memicu update visual"""
        # Set Font
        if "font_family" in t:
            self.font_combo.setCurrentFont(QFont(t["font_family"]))
        
        # Set Colors
        self.text_color_hex = t.get("text", "#ffffff")
        self.btn_text_color.setStyleSheet(f"background-color: {self.text_color_hex};")
        
        if "stroke_c" in t:
            self.stroke_color_hex = t["stroke_c"]
            self.btn_stroke_color.setStyleSheet(f"background-color: {self.stroke_color_hex};")

        if "bg_c" in t:
            self.bg_color_hex = t["bg_c"]
            self.btn_bg_color.setStyleSheet(f"background-color: {self.bg_color_hex};")

        # Set Toggles
        self.chk_stroke.setChecked(t.get("stroke_on", False))
        self.spn_stroke.setValue(t.get("stroke_w", 2))
        self.chk_bg.setChecked(t.get("bg_on", False))
        
        # Simpan metadata tambahan ke settings internal jika perlu (shadow, spacing, rounded)
        # Kita kirim semua data ini melalui signal
        self._emit_style_update(extra_props=t)

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
        if extra_props:
            data.update(extra_props)
        self.sig_style_changed.emit(data)

    def _init_api_section(self):
        group = QGroupBox("AUTO GENERATION")
        group.setStyleSheet("QGroupBox { font-weight: bold; color: #d19a66; }")
        grid = QGridLayout(group)
        
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setPlaceholderText("AssemblyAI API Key...")
        self.txt_api_key.setEchoMode(QLineEdit.Password)
        self.txt_api_key.setStyleSheet("background-color: #2b2b2b; color: #dcdcdc; border: 1px solid #3e4451;")

        self.btn_generate = QPushButton("🚀 GENERATE CAPTION")
        self.btn_generate.setFixedHeight(30)
        self.btn_generate.setStyleSheet("background-color: #d19a66; color: #21252b; font-weight: bold;")
        
        grid.addWidget(QLabel("API Key:"), 0, 0)
        grid.addWidget(self.txt_api_key, 0, 1)
        grid.addWidget(self.btn_generate, 1, 0, 1, 2)
        self.layout.addWidget(group)

    def _init_styling_section(self):
        group = QGroupBox("STYLE PROPERTIES")
        group.setStyleSheet("QGroupBox { color: #61afef; font-weight: bold; }")
        grid = QGridLayout(group)

        self.font_combo = QFontComboBox()
        self.spn_size = QSpinBox()
        self.spn_size.setRange(10, 500); self.spn_size.setValue(45)

        self.btn_text_color = self._create_color_btn(self.text_color_hex)
        self.btn_text_color.clicked.connect(lambda: self._pick_color("text"))

        self.chk_stroke = QCheckBox("Stroke")
        self.spn_stroke = QSpinBox(); self.spn_stroke.setRange(0, 50)
        self.btn_stroke_color = self._create_color_btn(self.stroke_color_hex)
        self.btn_stroke_color.clicked.connect(lambda: self._pick_color("stroke"))

        self.chk_bg = QCheckBox("Bg Box")
        self.btn_bg_color = self._create_color_btn(self.bg_color_hex)
        self.btn_bg_color.clicked.connect(lambda: self._pick_color("bg"))

        grid.addWidget(QLabel("Font:"), 0, 0); grid.addWidget(self.font_combo, 0, 1, 1, 3)
        grid.addWidget(QLabel("Size:"), 1, 0); grid.addWidget(self.spn_size, 1, 1)
        grid.addWidget(QLabel("Color:"), 1, 2); grid.addWidget(self.btn_text_color, 1, 3)
        grid.addWidget(self.chk_stroke, 2, 0); grid.addWidget(self.spn_stroke, 2, 1)
        grid.addWidget(QLabel("Str Color:"), 2, 2); grid.addWidget(self.btn_stroke_color, 2, 3)
        grid.addWidget(self.chk_bg, 3, 0); grid.addWidget(self.btn_bg_color, 3, 3)

        self.layout.addWidget(group)

    def _create_color_btn(self, hex_c):
        btn = QPushButton()
        btn.setFixedSize(40, 20)
        btn.setStyleSheet(f"background-color: {hex_c}; border: 1px solid #5c6370; border-radius: 2px;")
        return btn

    def _on_master_toggle(self, checked):
        self.content_wrapper.setEnabled(checked)
        self.sig_enable_toggled.emit(checked)
        self.chk_enable_caption.setText("✅ ENABLE CAPTION LAYER" if checked else "❌ CAPTION DISABLED")

    def _pick_color(self, target):
        from PySide6.QtWidgets import QColorDialog
        c = QColorDialog.getColor()
        if c.isValid():
            hex_c = c.name()
            if target == "text": self.text_color_hex = hex_c; self.btn_text_color.setStyleSheet(f"background-color: {hex_c};")
            elif target == "stroke": self.stroke_color_hex = hex_c; self.btn_stroke_color.setStyleSheet(f"background-color: {hex_c};")
            elif target == "bg": self.bg_color_hex = hex_c; self.btn_bg_color.setStyleSheet(f"background-color: {hex_c};")
            self._emit_style_update()

    def _connect_signals(self):
        self.font_combo.currentFontChanged.connect(self._emit_style_update)
        self.spn_size.valueChanged.connect(self._emit_style_update)
        self.chk_stroke.toggled.connect(self._emit_style_update)
        self.spn_stroke.valueChanged.connect(self._emit_style_update)
        self.chk_bg.toggled.connect(self._emit_style_update)
