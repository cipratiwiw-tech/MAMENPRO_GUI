from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, QSpinBox, 
                             QPushButton, QTextEdit, QScrollArea, QCheckBox, 
                             QHBoxLayout, QFontComboBox, QButtonGroup, QColorDialog, 
                             QDoubleSpinBox, QGridLayout, QAbstractSpinBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QFontMetrics

class TextTab(QScrollArea):
    sig_text_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        container = QWidget()
        container.setStyleSheet("background-color: #23272e;") 
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(8, 8, 8, 8)
        
        # [STYLE] Compact Input
        self.spinbox_style = """
            QSpinBox, QDoubleSpinBox {
                background-color: #2b2b2b;
                color: #dcdcdc;
                border: 1px solid #3e4451;
                border-radius: 2px;
                padding-left: 0px;  
                padding-right: 4px; 
                margin: 0px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #56b6c2;
                background-color: #1e1e1e;
            }
        """
        
        # Inisialisasi variabel warna DEFAULT untuk mencegah AttributeError
        self.text_color_hex = "#ffffff"
        self.stroke_color_hex = "#000000"
        self.bg_color_hex = "#000000"
        self.shadow_color_hex = "#555555"

        # [BARU] 1. Panel Waktu (Timing)
        self._init_time_attributes()
        
        self._init_text_style()
        self._init_paragraph_style()
        
        self.layout.addStretch()
        self.setWidget(container)
        self._connect_signals()

    # --- HELPER FUNCTIONS ---
    def _create_label(self, text):
        """Label Rata Kanan"""
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet("color: #abb2bf; font-size: 11px; margin-right: 4px;") 
        return lbl

    def _optimize_width(self, sb, min_val, max_val, suffix):
        """Hitung lebar pixel optimal"""
        if isinstance(sb, QDoubleSpinBox):
            prec = sb.decimals()
            s_min = f"{min_val:.{prec}f}{suffix}"
            s_max = f"{max_val:.{prec}f}{suffix}"
        else:
            s_min = f"{min_val}{suffix}"
            s_max = f"{max_val}{suffix}"
            
        longest_text = s_max if len(s_max) > len(s_min) else s_min
        fm = sb.fontMetrics()
        text_width = fm.horizontalAdvance(longest_text)
        final_width = max(45, text_width + 24)
        sb.setFixedWidth(final_width)

    def _style_spinbox(self, sb, min_v, max_v, suffix):
        """Apply compact style & calculate width"""
        sb.setButtonSymbols(QAbstractSpinBox.NoButtons) 
        sb.setAlignment(Qt.AlignRight) 
        sb.setStyleSheet(self.spinbox_style)
        self._optimize_width(sb, min_v, max_v, suffix)

    def _create_spinbox(self, min_v, max_v, val, suffix=""):
        sb = QSpinBox()
        sb.setRange(min_v, max_v); sb.setValue(val); sb.setSuffix(suffix)
        self._style_spinbox(sb, min_v, max_v, suffix)
        return sb
    
    def _create_double_spinbox(self, min_v, max_v, val, suffix="s"):
        sb = QDoubleSpinBox()
        sb.setRange(min_v, max_v); sb.setValue(val); sb.setSuffix(suffix)
        sb.setSingleStep(0.1)
        self._style_spinbox(sb, min_v, max_v, suffix)
        return sb
    
    def _create_color_btn(self, hex_color):
        btn = QPushButton("")
        btn.setFixedWidth(40) # Kotak kecil
        btn.setFixedHeight(20)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #5c6370; border-radius: 2px;")
        return btn

    def _create_align_btn(self, icon_text, tooltip):
        btn = QPushButton(icon_text)
        btn.setCheckable(True)
        btn.setFixedWidth(30)
        btn.setToolTip(tooltip)
        btn.setStyleSheet("""
            QPushButton { background-color: #2b2b2b; color: #abb2bf; border: 1px solid #3e4451; margin: 0px; }
            QPushButton:checked { background-color: #56b6c2; color: #282c34; border: 1px solid #56b6c2; }
            QPushButton:hover { background-color: #3e4451; }
        """)
        return btn

    # --- INITIALIZATION ---
    def _init_time_attributes(self):
        self.group_time = QGroupBox("TIMING")
        self.group_time.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #e1b12c; margin-top: 6px; color: #e1b12c; }")
        
        grid = QGridLayout(self.group_time)
        grid.setSpacing(8)
        grid.setContentsMargins(5, 10, 5, 5)
        
        self.spn_start = self._create_double_spinbox(0.0, 36000.0, 0.0, "s")
        self.spn_end = self._create_double_spinbox(0.0, 36000.0, 5.0, "s")
        
        grid.addWidget(self._create_label("Start:"), 0, 0)
        grid.addWidget(self.spn_start, 0, 1)
        grid.addWidget(self._create_label("End:"), 0, 2)
        grid.addWidget(self.spn_end, 0, 3)
        
        grid.setColumnStretch(4, 1) 
        self.layout.addWidget(self.group_time)
        
    def _init_text_style(self):
        group = QGroupBox("CONTENT & STYLE")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #c678dd; margin-top: 6px; color: #c678dd; }")
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 10, 5, 5)
                
        # 1. Konten Teks
        lbl_content = QLabel("TEXT CONTENT")
        lbl_content.setStyleSheet("color: #5c6370; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(lbl_content)

        self.txt_input = QTextEdit()
        self.txt_input.setPlaceholderText("Type here...")
        self.txt_input.setMaximumHeight(60)
        self.txt_input.setStyleSheet("background-color: #2b2b2b; color: #dcdcdc; border: 1px solid #3e4451; border-radius: 3px;")
        layout.addWidget(self.txt_input)
        
        # 2. Font Properties (Grid Layout)
        grid_font = QGridLayout()
        grid_font.setSpacing(8)

        # Font Family
        self.font_combo = QFontComboBox()
        self.font_combo.setFont(QFont("Segoe UI", 9))
        self.font_combo.setStyleSheet("""
            QFontComboBox { background-color: #2b2b2b; color: #dcdcdc; border: 1px solid #3e4451; padding: 2px; }
            QFontComboBox::drop-down { border: none; }
        """)
        
        grid_font.addWidget(self._create_label("Font:"), 0, 0)
        grid_font.addWidget(self.font_combo, 0, 1, 1, 3) # Span 3 col

        # Size & Rot (Baris 2)
        self.spn_size = self._create_spinbox(8, 500, 60, " px")
        self.spn_rot = self._create_spinbox(-360, 360, 0, "°")
        
        grid_font.addWidget(self._create_label("Size:"), 1, 0)
        grid_font.addWidget(self.spn_size, 1, 1)
        grid_font.addWidget(self._create_label("Rot:"), 1, 2)
        grid_font.addWidget(self.spn_rot, 1, 3)

        # Text Color Button 
        self.btn_text_color = QPushButton("Color")
        self.btn_text_color.setCursor(Qt.PointingHandCursor)
        self.btn_text_color.setStyleSheet(f"background-color: {self.text_color_hex}; color: black; font-weight:bold; border-radius: 2px; border: 1px solid #5c6370;")
        self.btn_text_color.clicked.connect(lambda: self._pick_color("text"))
        
        grid_font.addWidget(self.btn_text_color, 1, 4)
        
        layout.addLayout(grid_font)
        
        # Separator
        line = QLabel(); line.setFixedHeight(1); line.setStyleSheet("background-color: #3e4451;")
        layout.addWidget(line)

        # 3. Decoration (Stroke, BG, Shadow) - Grid Compact
        grid_deco = QGridLayout()
        grid_deco.setSpacing(8)

        # -- Stroke --
        self.chk_stroke = QCheckBox("Stroke")
        self.chk_stroke.setStyleSheet("color: #abb2bf;")
        self.spn_stroke = self._create_spinbox(0, 50, 0, "px")
        self.btn_stroke_color = self._create_color_btn(self.stroke_color_hex)
        self.btn_stroke_color.clicked.connect(lambda: self._pick_color("stroke"))
        
        grid_deco.addWidget(self.chk_stroke, 0, 0)
        grid_deco.addWidget(self._create_label("Width:"), 0, 1)
        grid_deco.addWidget(self.spn_stroke, 0, 2)
        grid_deco.addWidget(self.btn_stroke_color, 0, 3)

        # -- Background --
        self.chk_bg = QCheckBox("Background")
        self.chk_bg.setStyleSheet("color: #abb2bf;")
        self.btn_bg_color = self._create_color_btn(self.bg_color_hex)
        self.btn_bg_color.clicked.connect(lambda: self._pick_color("bg"))
        
        grid_deco.addWidget(self.chk_bg, 1, 0)
        grid_deco.addWidget(self.btn_bg_color, 1, 3) # Align right

        # -- Shadow --
        self.chk_shadow = QCheckBox("Shadow")
        self.chk_shadow.setStyleSheet("color: #abb2bf;")
        self.btn_shadow_color = self._create_color_btn(self.shadow_color_hex)
        self.btn_shadow_color.clicked.connect(lambda: self._pick_color("shadow"))

        grid_deco.addWidget(self.chk_shadow, 2, 0)
        grid_deco.addWidget(self.btn_shadow_color, 2, 3)

        layout.addLayout(grid_deco)
        self.layout.addWidget(group)

    def _init_paragraph_style(self):
        group = QGroupBox("PARAGRAPH")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #98c379; margin-top: 6px; color: #98c379; }")
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 10, 5, 5)
        
        # Alignment Row
        row_align = QHBoxLayout()
        row_align.setSpacing(0) # Gabung tombol
        
        self.btn_align_left = self._create_align_btn("⬅", "Left")
        self.btn_align_center = self._create_align_btn("↔", "Center")
        self.btn_align_right = self._create_align_btn("➡", "Right")
        self.btn_align_justify = self._create_align_btn("≣", "Justify")
        
        self.align_group = QButtonGroup(self)
        self.align_group.addButton(self.btn_align_left, 1)
        self.align_group.addButton(self.btn_align_center, 2)
        self.align_group.addButton(self.btn_align_right, 3)
        self.align_group.addButton(self.btn_align_justify, 4)
        
        self.btn_align_center.setChecked(True)
        
        row_align.addWidget(self.btn_align_left)
        row_align.addWidget(self.btn_align_center)
        row_align.addWidget(self.btn_align_right)
        row_align.addWidget(self.btn_align_justify)
        row_align.addStretch() 
        
        # Line Spacing compact
        self.spn_line_height = self._create_spinbox(0, 300, 100, "%")
        lbl_line = self._create_label("Line Height:")
        
        row_align.addWidget(lbl_line)
        row_align.addWidget(self.spn_line_height)
        
        layout.addLayout(row_align)
        self.layout.addWidget(group)

    def _pick_color(self, target):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_c = color.name()
            if target == "text":
                self.text_color_hex = hex_c
                # Kontras text button
                fg_col = 'white' if color.lightness() < 128 else 'black'
                self.btn_text_color.setStyleSheet(f"background-color: {hex_c}; color: {fg_col}; font-weight:bold; border-radius: 2px; border: 1px solid #5c6370;")
            elif target == "stroke":
                self.stroke_color_hex = hex_c
                self.btn_stroke_color.setStyleSheet(f"background-color: {hex_c}; border: 1px solid #5c6370; border-radius: 2px;")
            elif target == "bg":
                self.bg_color_hex = hex_c
                self.btn_bg_color.setStyleSheet(f"background-color: {hex_c}; border: 1px solid #5c6370; border-radius: 2px;")
            elif target == "shadow":
                self.shadow_color_hex = hex_c
                self.btn_shadow_color.setStyleSheet(f"background-color: {hex_c}; border: 1px solid #5c6370; border-radius: 2px;")
            self._emit_change()

    def _connect_signals(self):
        # Time Signals
        self.spn_start.valueChanged.connect(self._emit_change)
        self.spn_end.valueChanged.connect(self._emit_change)

        # Text Signals
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
            "start_time": self.spn_start.value(),
            "end_time": self.spn_end.value(),
            "text_content": self.txt_input.toPlainText(),
            "font": self.font_combo.currentFont().family(),
            "font_size": self.spn_size.value(),
            "rotation": self.spn_rot.value(),
            "text_color": self.text_color_hex,
            "stroke_on": self.chk_stroke.isChecked(),
            "stroke_width": self.spn_stroke.value(),
            "stroke_color": self.stroke_color_hex, # Sekarang variabel ini sudah ada!
            "bg_on": self.chk_bg.isChecked(),
            "bg_color": self.bg_color_hex,         # Ini juga
            "shadow_on": self.chk_shadow.isChecked(),
            "shadow_color": self.shadow_color_hex, # Ini juga
            "alignment": align,
            "line_spacing": self.spn_line_height.value()
        }
        self.sig_text_changed.emit(data)

    def set_values(self, data):
        self.blockSignals(True)
        
        if "start_time" in data:
            self.spn_start.setValue(float(data["start_time"]))
        
        if "end_time" in data and data["end_time"] is not None:
            self.spn_end.setValue(float(data["end_time"]))
        else:
            self.spn_end.setValue(self.spn_start.value() + 5.0)
            
        if "text_content" in data: 
            self.txt_input.setText(data["text_content"])
        
        if "font_size" in data: self.spn_size.setValue(data["font_size"])
        if "rotation" in data: self.spn_rot.setValue(data["rotation"])
        
        # Colors
        if "text_color" in data:
            self.text_color_hex = data["text_color"]
            c = data["text_color"]
            self.btn_text_color.setStyleSheet(f"background-color: {c}; font-weight:bold; border-radius: 2px; border: 1px solid #5c6370;")
        
        if "stroke_on" in data: self.chk_stroke.setChecked(data["stroke_on"])
        if "stroke_width" in data: self.spn_stroke.setValue(data["stroke_width"])
        if "stroke_color" in data:
             self.stroke_color_hex = data["stroke_color"]
             self.btn_stroke_color.setStyleSheet(f"background-color: {self.stroke_color_hex}; border: 1px solid #5c6370; border-radius: 2px;")
        
        if "bg_on" in data: self.chk_bg.setChecked(data["bg_on"])
        if "bg_color" in data:
            self.bg_color_hex = data["bg_color"]
            self.btn_bg_color.setStyleSheet(f"background-color: {self.bg_color_hex}; border: 1px solid #5c6370; border-radius: 2px;")

        if "shadow_on" in data: self.chk_shadow.setChecked(data["shadow_on"])
        if "shadow_color" in data:
             self.shadow_color_hex = data["shadow_color"]
             self.btn_shadow_color.setStyleSheet(f"background-color: {self.shadow_color_hex}; border: 1px solid #5c6370; border-radius: 2px;")
        
        # Alignment
        if "alignment" in data:
            align = data["alignment"]
            if align == "left": self.btn_align_left.setChecked(True)
            elif align == "right": self.btn_align_right.setChecked(True)
            elif align == "justify": self.btn_align_justify.setChecked(True)
            else: self.btn_align_center.setChecked(True)
            
        if "line_spacing" in data:
            self.spn_line_height.setValue(data["line_spacing"])

        self.blockSignals(False)