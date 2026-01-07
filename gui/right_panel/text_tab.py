from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, QSpinBox, 
                             QPushButton, QComboBox, QTextEdit, QScrollArea, 
                             QCheckBox, QHBoxLayout, QFontComboBox, QLineEdit, 
                             QButtonGroup, QColorDialog)
from PySide6.QtCore import Qt, Signal

class TextTab(QScrollArea):
    # Signal dikirim saat ada perubahan apapun di UI
    sig_text_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(15)
        
        # --- 1. PANEL ATAS: GAYA TEKS ---
        self._init_text_style()
        
        # --- 2. PANEL BAWAH: PARAGRAF ---
        self._init_paragraph_style()
        
        self.layout.addStretch()
        self.setWidget(container)

        # Connect semua input ke fungsi emit
        self._connect_signals()

    def _init_text_style(self):
        group = QGroupBox("GAYA TEKS")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # 1. Konten Teks
        self.txt_content = QLineEdit("Mamen Pro Editor")
        self.txt_content.setPlaceholderText("Ketik Teks Utama di sini...")
        layout.addWidget(QLabel("Konten Teks:"))
        layout.addWidget(self.txt_content)
        
        # 2. Font
        self.font_combo = QFontComboBox()
        layout.addWidget(QLabel("Jenis Font:"))
        layout.addWidget(self.font_combo)
        
        # 3. Ukuran & Warna Teks
        row_size = QHBoxLayout()
        self.spn_size = QSpinBox()
        self.spn_size.setRange(8, 500)
        self.spn_size.setValue(60)
        self.spn_size.setSuffix(" px")
        self.spn_size.setPrefix("Size: ")
        
        self.btn_text_color = QPushButton("Warna Teks")
        self.btn_text_color.setStyleSheet("background-color: #ffffff; color: black; text-align: center;")
        self.text_color_hex = "#ffffff"
        self.btn_text_color.clicked.connect(lambda: self._pick_color("text"))

        row_size.addWidget(self.spn_size)
        row_size.addWidget(self.btn_text_color)
        layout.addLayout(row_size)
        
        # 4. Stroke
        row_stroke = QHBoxLayout()
        self.chk_stroke = QCheckBox("Stroke")
        
        self.spn_stroke = QSpinBox()
        self.spn_stroke.setRange(0, 50)
        self.spn_stroke.setPrefix("Tebal: ")
        
        self.btn_stroke_color = QPushButton("Warna")
        self.btn_stroke_color.setFixedWidth(60)
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

        # 6. Shadow (Dipertahankan dari file lama)
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
        group = QGroupBox("PARAGRAF")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # 1. Kotak Input Paragraf
        self.txt_area = QTextEdit()
        self.txt_area.setPlaceholderText("Ketik paragraf panjang di sini...")
        self.txt_area.setMaximumHeight(80)
        layout.addWidget(self.txt_area)
        
        # 2. Align Icons + Spacing (Dipertahankan dari file lama)
        row_align = QHBoxLayout()
        
        self.btn_align_left = QPushButton("⬅")
        self.btn_align_center = QPushButton("↔")
        self.btn_align_right = QPushButton("➡")
        self.btn_align_justify = QPushButton("≣")
        
        # Grouping agar hanya satu yang aktif
        self.align_group = QButtonGroup(self)
        self.align_group.addButton(self.btn_align_left, 1) # Id 1
        self.align_group.addButton(self.btn_align_center, 2) # Id 2
        self.align_group.addButton(self.btn_align_right, 3) # Id 3
        self.align_group.addButton(self.btn_align_justify, 4) # Id 4
        
        for btn in self.align_group.buttons():
            btn.setCheckable(True)
            btn.setFixedWidth(30)
            
        self.btn_align_left.setChecked(True) # Default
        
        # Spacing
        self.spn_line_height = QSpinBox()
        self.spn_line_height.setRange(0, 200)
        self.spn_line_height.setValue(100)
        self.spn_line_height.setPrefix("Spasi: ")
        
        row_align.addWidget(self.btn_align_left)
        row_align.addWidget(self.btn_align_center)
        row_align.addWidget(self.btn_align_right)
        row_align.addWidget(self.btn_align_justify)
        row_align.addWidget(self.spn_line_height)
        layout.addLayout(row_align)
        
        # 3. Warna Background Paragraf (Dipertahankan)
        self.btn_para_bg = QPushButton("Warna Background Paragraf")
        self.btn_para_bg.setStyleSheet("background-color: transparent; color: black;") # Default
        self.para_bg_hex = "#ffffff" # Default assumption
        self.btn_para_bg.clicked.connect(lambda: self._pick_color("para_bg"))
        layout.addWidget(self.btn_para_bg)
        
        self.layout.addWidget(group)

    def _pick_color(self, target):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_c = color.name()
            if target == "text":
                self.text_color_hex = hex_c
                self.btn_text_color.setStyleSheet(f"background-color: {hex_c}; color: {'black' if color.lightness() > 128 else 'white'};")
            elif target == "stroke":
                self.stroke_color_hex = hex_c
                self.btn_stroke_color.setStyleSheet(f"background-color: {hex_c}; color: {'black' if color.lightness() > 128 else 'white'};")
            elif target == "bg":
                self.bg_color_hex = hex_c
                self.btn_bg_color.setStyleSheet(f"background-color: {hex_c}; color: {'black' if color.lightness() > 128 else 'white'};")
            elif target == "shadow":
                self.shadow_color_hex = hex_c
                self.btn_shadow_color.setStyleSheet(f"background-color: {hex_c}; color: {'black' if color.lightness() > 128 else 'white'};")
            elif target == "para_bg":
                self.para_bg_hex = hex_c
                self.btn_para_bg.setStyleSheet(f"background-color: {hex_c}; color: {'black' if color.lightness() > 128 else 'white'};")
            
            self._emit_change()

    def _connect_signals(self):
        # Trigger emit saat ada perubahan nilai
        self.txt_content.textChanged.connect(self._emit_change)
        self.font_combo.currentFontChanged.connect(self._emit_change)
        self.spn_size.valueChanged.connect(self._emit_change)
        
        # Stroke
        self.chk_stroke.toggled.connect(self._emit_change)
        self.spn_stroke.valueChanged.connect(self._emit_change)
        
        # BG Text
        self.chk_bg.toggled.connect(self._emit_change)
        
        # Shadow
        self.chk_shadow.toggled.connect(self._emit_change)
        
        # Paragraph
        self.txt_area.textChanged.connect(self._emit_change)
        self.align_group.buttonClicked.connect(self._emit_change) # Button Group signal
        self.spn_line_height.valueChanged.connect(self._emit_change)

    def _emit_change(self):
        # Tentukan alignment
        align = "left"
        if self.btn_align_center.isChecked(): align = "center"
        elif self.btn_align_right.isChecked(): align = "right"
        elif self.btn_align_justify.isChecked(): align = "justify"

        data = {
            # --- Text Style Data ---
            "text_content": self.txt_content.text(),
            "font": self.font_combo.currentFont().family(),
            "font_size": self.spn_size.value(),
            "text_color": self.text_color_hex,
            
            "stroke_on": self.chk_stroke.isChecked(),
            "stroke_width": self.spn_stroke.value(),
            "stroke_color": self.stroke_color_hex,
            
            "bg_on": self.chk_bg.isChecked(),
            "bg_color": self.bg_color_hex,
            
            "shadow_on": self.chk_shadow.isChecked(),
            "shadow_color": self.shadow_color_hex,
            
            # --- Paragraph Data ---
            "paragraph_content": self.txt_area.toPlainText(),
            "alignment": align,
            "line_spacing": self.spn_line_height.value(),
            "paragraph_bg_color": self.para_bg_hex
        }
        self.sig_text_changed.emit(data)

    def set_values(self, data):
        """Menerima data dari luar untuk mengupdate UI (Two-way binding)"""
        self.blockSignals(True)
        
        if "text_content" in data: self.txt_content.setText(data["text_content"])
        if "paragraph_content" in data: self.txt_area.setText(data["paragraph_content"])
        if "font_size" in data: self.spn_size.setValue(data["font_size"])
        # ... (Tambahkan logic set lain sesuai kebutuhan) ...
        
        self.blockSignals(False)