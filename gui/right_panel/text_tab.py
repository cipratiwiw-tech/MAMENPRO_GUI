from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, QSpinBox, 
                             QPushButton, QComboBox, QTextEdit, QScrollArea, 
                             QCheckBox, QHBoxLayout, QFontComboBox, QLineEdit, 
                             QButtonGroup, QColorDialog, QFontComboBox, QFontDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class TextTab(QScrollArea):
    sig_text_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(15)
        
        self._init_text_style()
        self._init_paragraph_style()
        
        self.layout.addStretch()
        self.setWidget(container)
        self._connect_signals()

    def _init_text_style(self):
        group = QGroupBox("GAYA TEKS & KONTEN")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        # Di dalam _init_text_style pada text_tab.py
        self.font_combo = QFontComboBox()
        # Tambahkan baris ini untuk memastikan ukuran awal valid
        self.font_combo.setFont(QFont("Segoe UI", 12)) 
        layout.addWidget(QLabel("Jenis Font:"))
        layout.addWidget(self.font_combo)
        
        # 1. Konten Teks (Unified Input)
        # Menggantikan QLineEdit lama dengan QTextEdit 4 baris
        layout.addWidget(QLabel("Isi Teks / Paragraf:"))
        self.txt_input = QTextEdit()
        self.txt_input.setPlaceholderText("Ketik teks di sini...")
        self.txt_input.setMaximumHeight(80) # Kira-kira 4 baris
        layout.addWidget(self.txt_input)
        
        # 2. Font & Style
        self.font_combo = QFontComboBox()
        layout.addWidget(QLabel("Jenis Font:"))
        layout.addWidget(self.font_combo)
        
        # 3. Ukuran, Rotasi & Warna Teks
        row_prop = QHBoxLayout()
        self.spn_size = QSpinBox()
        self.spn_size.setRange(8, 500); self.spn_size.setValue(60)
        self.spn_size.setSuffix(" px"); self.spn_size.setPrefix("Size: ")
        
        self.spn_rot = QSpinBox()
        self.spn_rot.setRange(-360, 360); self.spn_rot.setValue(0)
        self.spn_rot.setSuffix("°"); self.spn_rot.setPrefix("Rot: ")

        self.btn_text_color = QPushButton("Warna Teks")
        self.btn_text_color.setStyleSheet("background-color: #ffffff; color: black; font-weight:bold;")
        self.text_color_hex = "#ffffff"
        self.btn_text_color.clicked.connect(lambda: self._pick_color("text"))

        row_prop.addWidget(self.spn_size)
        row_prop.addWidget(self.spn_rot)
        row_prop.addWidget(self.btn_text_color)
        layout.addLayout(row_prop)
        
        # 4. Stroke
        row_stroke = QHBoxLayout()
        self.chk_stroke = QCheckBox("Stroke")
        self.spn_stroke = QSpinBox()
        self.spn_stroke.setRange(0, 50)
        self.spn_stroke.setPrefix("Tebal: ")
        self.btn_stroke_color = QPushButton("Warna")
        self.btn_stroke_color.setStyleSheet("background-color: #000000; color: white;")
        self.stroke_color_hex = "#000000"
        self.btn_stroke_color.clicked.connect(lambda: self._pick_color("stroke"))
        
        row_stroke.addWidget(self.chk_stroke)
        row_stroke.addWidget(self.spn_stroke)
        row_stroke.addWidget(self.btn_stroke_color)
        layout.addLayout(row_stroke)
        
        # 5. Background Text
        row_bg = QHBoxLayout()
        self.chk_bg = QCheckBox("Background")
        self.btn_bg_color = QPushButton("Warna BG")
        self.btn_bg_color.setStyleSheet("background-color: #000000; color: white;")
        self.bg_color_hex = "#000000"
        self.btn_bg_color.clicked.connect(lambda: self._pick_color("bg"))
        row_bg.addWidget(self.chk_bg)
        row_bg.addWidget(self.btn_bg_color)
        layout.addLayout(row_bg)

        # 6. Shadow
        row_shadow = QHBoxLayout()
        self.chk_shadow = QCheckBox("Shadow")
        self.btn_shadow_color = QPushButton("Warna Shadow")
        self.btn_shadow_color.setStyleSheet("background-color: #555555; color: white;")
        self.shadow_color_hex = "#555555"
        self.btn_shadow_color.clicked.connect(lambda: self._pick_color("shadow"))
        row_shadow.addWidget(self.chk_shadow)
        row_shadow.addWidget(self.btn_shadow_color)
        layout.addLayout(row_shadow)

        self.layout.addWidget(group)

    def _init_paragraph_style(self):
        group = QGroupBox("SETTING PARAGRAF (Khusus Mode Paragraf)")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # [HAPUS] Input Text di sini sudah dihapus sesuai request
        
        # Alignment
        row_align = QHBoxLayout()
        self.btn_align_left = QPushButton("⬅")
        self.btn_align_center = QPushButton("↔")
        self.btn_align_right = QPushButton("➡")
        self.btn_align_justify = QPushButton("≣")
        
        self.align_group = QButtonGroup(self)
        self.align_group.addButton(self.btn_align_left, 1)
        self.align_group.addButton(self.btn_align_center, 2)
        self.align_group.addButton(self.btn_align_right, 3)
        self.align_group.addButton(self.btn_align_justify, 4)
        
        for btn in self.align_group.buttons():
            btn.setCheckable(True)
            btn.setFixedWidth(40)
            
        self.btn_align_center.setChecked(True) # Default Center
        
        # Line Spacing
        self.spn_line_height = QSpinBox()
        self.spn_line_height.setRange(0, 200)
        self.spn_line_height.setValue(100)
        self.spn_line_height.setPrefix("Spasi Baris: ")
        
        row_align.addWidget(self.btn_align_left)
        row_align.addWidget(self.btn_align_center)
        row_align.addWidget(self.btn_align_right)
        row_align.addWidget(self.btn_align_justify)
        layout.addLayout(row_align)
        layout.addWidget(self.spn_line_height)
        
        self.layout.addWidget(group)

    def _pick_color(self, target):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_c = color.name()
            if target == "text":
                self.text_color_hex = hex_c
                self.btn_text_color.setStyleSheet(f"background-color: {hex_c}; color: {'white' if color.lightness() < 128 else 'black'}; font-weight:bold;")
            elif target == "stroke":
                self.stroke_color_hex = hex_c
                self.btn_stroke_color.setStyleSheet(f"background-color: {hex_c};")
            elif target == "bg":
                self.bg_color_hex = hex_c
                self.btn_bg_color.setStyleSheet(f"background-color: {hex_c};")
            elif target == "shadow":
                self.shadow_color_hex = hex_c
                self.btn_shadow_color.setStyleSheet(f"background-color: {hex_c};")
            self._emit_change()

    def _connect_signals(self):
        self.txt_input.textChanged.connect(self._emit_change)
        self.font_combo.currentFontChanged.connect(self._emit_change)
        self.spn_size.valueChanged.connect(self._emit_change)
        self.spn_rot.valueChanged.connect(self._emit_change)
        self.chk_stroke.toggled.connect(self._emit_change)
        self.spn_stroke.valueChanged.connect(self._emit_change)
        self.chk_bg.toggled.connect(self._emit_change)
        self.chk_shadow.toggled.connect(self._emit_change)
        self.align_group.buttonClicked.connect(self._emit_change)
        self.spn_line_height.valueChanged.connect(self._emit_change)

    def _emit_change(self):
        align = "center" # Default
        if self.btn_align_left.isChecked(): align = "left"
        elif self.btn_align_right.isChecked(): align = "right"
        elif self.btn_align_justify.isChecked(): align = "justify"

        data = {
            "text_content": self.txt_input.toPlainText(), # Satu sumber input
            "font": self.font_combo.currentFont().family(),
            "font_size": self.spn_size.value(),
            "rotation": self.spn_rot.value(),
            "text_color": self.text_color_hex,
            "stroke_on": self.chk_stroke.isChecked(),
            "stroke_width": self.spn_stroke.value(),
            "stroke_color": self.stroke_color_hex,
            "bg_on": self.chk_bg.isChecked(),
            "bg_color": self.bg_color_hex,
            "shadow_on": self.chk_shadow.isChecked(),
            "shadow_color": self.shadow_color_hex,
            "alignment": align,
            "line_spacing": self.spn_line_height.value()
        }
        self.sig_text_changed.emit(data)

    def set_values(self, data):
        self.blockSignals(True)
        # Populate Text Input (Baik itu Text biasa atau Paragraf)
        if "text_content" in data: 
            self.txt_input.setText(data["text_content"])
        
        if "font_size" in data: self.spn_size.setValue(data["font_size"])
        if "rotation" in data: self.spn_rot.setValue(data["rotation"])
        
        # Colors
        if "text_color" in data:
            self.text_color_hex = data["text_color"]
            self.btn_text_color.setStyleSheet(f"background-color: {self.text_color_hex};")
        
        if "stroke_on" in data: self.chk_stroke.setChecked(data["stroke_on"])
        if "stroke_width" in data: self.spn_stroke.setValue(data["stroke_width"])
        
        if "bg_on" in data: self.chk_bg.setChecked(data["bg_on"])
        if "bg_color" in data:
            self.bg_color_hex = data["bg_color"]
            self.btn_bg_color.setStyleSheet(f"background-color: {self.bg_color_hex};")

        if "shadow_on" in data: self.chk_shadow.setChecked(data["shadow_on"])
        
        # Alignment
        if "alignment" in data:
            align = data["alignment"]
            if align == "left": self.btn_align_left.setChecked(True)
            elif align == "right": self.btn_align_right.setChecked(True)
            elif align == "justify": self.btn_align_justify.setChecked(True)
            else: self.btn_align_center.setChecked(True)

        self.blockSignals(False)