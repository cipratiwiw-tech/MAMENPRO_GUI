import os
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                             QLabel, QSpinBox, QPushButton, QComboBox, 
                             QTextEdit, QScrollArea, QCheckBox, QHBoxLayout, 
                             QFontComboBox, QLineEdit, QColorDialog, QAbstractSpinBox, QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QFontMetrics, QColor
from dotenv import load_dotenv

class CaptionTab(QScrollArea):
    # Sinyal komunikasi ke Main Window / Controller
    sig_generate_caption = Signal(dict) # Kirim opsi generate caption
    sig_style_changed = Signal(dict)    # Kirim perubahan style real-time
    sig_enable_toggled = Signal(bool)   # [BARU] Signal untuk toggle layer

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        
        # --- 0. INISIALISASI VARIABEL DEFAULT ---
        # Penting agar tidak error saat widget style dibuat
        self.text_color_hex = "#ffffff"
        self.bg_color_hex = "#000000"
        self.stroke_color_hex = "#000000"
        self.spinbox_style = """
            QSpinBox { background-color: #2b2b2b; color: #dcdcdc; border: 1px solid #3e4451; border-radius: 2px; }
            QSpinBox:focus { border: 1px solid #61afef; }
        """

        # --- 1. SETUP CONTAINER UTAMA ---
        main_container = QWidget()
        main_container.setStyleSheet("background-color: #23272e;")
        self.main_layout = QVBoxLayout(main_container)
        
        # --- 2. [BARU] MASTER TOGGLE (Paling Atas) ---
        self.chk_enable_caption = QCheckBox("✅ ENABLE CAPTION LAYER")
        self.chk_enable_caption.setStyleSheet("""
            QCheckBox { font-weight: bold; color: #abb2bf; font-size: 14px; padding: 8px; border-bottom: 1px solid #3e4451; }
            QCheckBox::indicator { width: 18px; height: 18px; }
            QCheckBox::checked { color: #98c379; }
        """)
        self.main_layout.addWidget(self.chk_enable_caption)

        # --- 3. [BARU] CONTENT WRAPPER ---
        # Semua widget settingan dimasukkan ke sini agar bisa di-disable massal
        self.content_wrapper = QWidget()
        self.layout = QVBoxLayout(self.content_wrapper) # self.layout tetap digunakan fungsi child
        self.layout.setContentsMargins(0,0,0,0)
        
        # --- 4. INISIALISASI GRUP WIDGET ---
        self._init_api_group()      # Grup API Key & Generate
        self._init_editor_group()   # Grup Editor Transcript
        self._init_style_group()    # Grup Styling (Font, Color, dll)
        
        # Masukkan wrapper ke layout utama
        self.main_layout.addWidget(self.content_wrapper)
        self.main_layout.addStretch()
        
        self.setWidget(main_container)
        
        # --- 5. STATE AWAL & KONEKSI ---
        # Default State: Mati (sesuai checkbox default unchecked)
        self.content_wrapper.setEnabled(False)
        self.chk_enable_caption.setChecked(False)
        self.chk_enable_caption.setText("❌ CAPTION DISABLED")

        # Connections
        self.chk_enable_caption.toggled.connect(self._on_master_toggle)
        self.btn_generate.clicked.connect(self._emit_generate) # Connect tombol generate
        self._connect_style_signals() # Connect sinyal style
    
    # --- LOGIC MASTER TOGGLE ---
    def _on_master_toggle(self, checked):
        """Logika saat tombol Enable ditekan"""
        self.content_wrapper.setEnabled(checked)
        self.sig_enable_toggled.emit(checked)
        
        # Feedback Visual
        if checked:
            self.chk_enable_caption.setText("✅ ENABLE CAPTION LAYER")
        else:
            self.chk_enable_caption.setText("❌ CAPTION DISABLED")

    # --- HELPER FUNCTIONS ---
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

    def _create_spinbox(self, min_v, max_v, val, suffix=""):
        sb = QSpinBox()
        sb.setRange(min_v, max_v); sb.setValue(val); sb.setSuffix(suffix)
        self._style_spinbox(sb, min_v, max_v, suffix)
        return sb
    
    def _create_color_btn(self, hex_color):
        btn = QPushButton("")
        btn.setFixedWidth(40)
        btn.setFixedHeight(20)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #5c6370; border-radius: 2px;")
        return btn

    # --- UI SECTIONS ---
    def _init_api_group(self):
        """Sebelumnya _init_auto_caption_group, di-rename agar konsisten dengan patch"""
        group = QGroupBox("AUTO GENERATION (ASSEMBLY AI)")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #d19a66; margin-top: 6px; color: #d19a66; }")
        
        grid = QGridLayout(group)
        grid.setSpacing(8)
        grid.setContentsMargins(5, 10, 5, 5)
        
        # Load API Key dari .env
        env_path = os.path.join(os.getcwd(), "engine", "caption", ".env")
        load_dotenv(env_path)
        saved_key = os.getenv("ASSEMBLYAI_API_KEY", "")

        # API Key Row
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setText(saved_key) 
        self.txt_api_key.setPlaceholderText("Paste API Key here...")
        self.txt_api_key.setEchoMode(QLineEdit.Password)
        self.txt_api_key.setStyleSheet("background-color: #2b2b2b; color: #dcdcdc; border: 1px solid #3e4451; border-radius: 2px;")
        
        self.btn_save_key = QPushButton("Save")
        self.btn_save_key.setFixedWidth(40)
        self.btn_save_key.setStyleSheet("background-color: #3e4451; color: #dcdcdc; border: none; border-radius: 2px;")
        
        grid.addWidget(self._create_label("Key:"), 0, 0)
        grid.addWidget(self.txt_api_key, 0, 1)
        grid.addWidget(self.btn_save_key, 0, 2)
        
        # Language & Generate
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Indonesia", "English"])
        self.combo_lang.setStyleSheet("background-color: #2b2b2b; color: #dcdcdc; border: 1px solid #3e4451;")
        
        self.btn_generate = QPushButton("GENERATE / PREVIEW CAPTION")
        self.btn_generate.setFixedHeight(30)
        self.btn_generate.setStyleSheet("background-color: #d19a66; color: #21252b; font-weight: bold; border: none; border-radius: 3px;")
        
        grid.addWidget(self._create_label("Lang:"), 1, 0)
        grid.addWidget(self.combo_lang, 1, 1)
        grid.addWidget(self.btn_generate, 1, 2) # Tombol di baris ke-1, kolom 2
        
        # Tombol generate full width di baris 4 (opsional layout)
        grid.addWidget(self.btn_generate, 2, 0, 1, 3) 
        
        self.layout.addWidget(group)

    def _init_editor_group(self):
        group = QGroupBox("TRANSCRIPT EDITOR")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #56b6c2; margin-top: 6px; color: #56b6c2; }")
        vbox = QVBoxLayout(group)
        vbox.setSpacing(8)
        vbox.setContentsMargins(5, 10, 5, 5)
        
        self.txt_editor = QTextEdit()
        self.txt_editor.setPlaceholderText("00:00 - Text...\n00:05 - Text...")
        self.txt_editor.setMaximumHeight(80)
        self.txt_editor.setStyleSheet("background-color: #2b2b2b; color: #98c379; border: 1px solid #3e4451; font-family: Consolas; font-size: 11px;")
        vbox.addWidget(self.txt_editor)
        
        hbox_btn = QHBoxLayout()
        self.btn_import = QPushButton("Import SRT")
        self.btn_export = QPushButton("Export SRT")
        for b in [self.btn_import, self.btn_export]:
            b.setStyleSheet("background-color: #3e4451; color: #dcdcdc; border-radius: 2px; padding: 2px;")
            hbox_btn.addWidget(b)
        
        vbox.addLayout(hbox_btn)
        self.layout.addWidget(group)

    def _init_style_group(self):
        group = QGroupBox("STYLE & APPEARANCE")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #c678dd; margin-top: 6px; color: #c678dd; }")
        
        grid = QGridLayout(group)
        grid.setSpacing(8)
        grid.setContentsMargins(5, 10, 5, 5)

        # 1. Activation Checkbox (Preview)
        self.chk_active = QCheckBox("Enable Preview")
        self.chk_active.setStyleSheet("color: #e06c75; font-weight: bold;")
        grid.addWidget(self.chk_active, 0, 0, 1, 2)

        # 2. Preset
        self.combo_preset = QComboBox()
        self.combo_preset.addItems(["Custom", "Karaoke", "Netflix", "Youtube Shorts", "Cinematic"])
        self.combo_preset.setStyleSheet("background-color: #2b2b2b; color: #dcdcdc; border: 1px solid #3e4451;")
        grid.addWidget(self._create_label("Preset:"), 0, 2)
        grid.addWidget(self.combo_preset, 0, 3)

        # 3. Font Attributes
        self.font_combo = QFontComboBox()
        self.font_combo.setFont(QFont("Segoe UI", 9))
        self.font_combo.setStyleSheet("background-color: #2b2b2b; color: #dcdcdc; border: none;")
        
        self.spn_size = self._create_spinbox(8, 200, 24, " px")
        
        grid.addWidget(self._create_label("Font:"), 1, 0)
        grid.addWidget(self.font_combo, 1, 1, 1, 3) 
        
        grid.addWidget(self._create_label("Size:"), 2, 0)
        grid.addWidget(self.spn_size, 2, 1)

        # 4. Colors (Text & BG)
        self.btn_text_color = self._create_color_btn(self.text_color_hex)
        self.btn_text_color.clicked.connect(lambda: self._pick_color("text"))
        
        self.btn_bg_color = self._create_color_btn(self.bg_color_hex)
        self.btn_bg_color.clicked.connect(lambda: self._pick_color("bg"))
        
        grid.addWidget(self._create_label("Text Color:"), 2, 2)
        grid.addWidget(self.btn_text_color, 2, 3)
        
        grid.addWidget(self._create_label("BG Color:"), 3, 2)
        grid.addWidget(self.btn_bg_color, 3, 3)
        
        # 5. Stroke
        self.chk_stroke = QCheckBox("Stroke")
        self.chk_stroke.setStyleSheet("color: #abb2bf;")
        self.spn_stroke = self._create_spinbox(0, 20, 0, "px")
        
        self.btn_stroke_color = self._create_color_btn(self.stroke_color_hex)
        self.btn_stroke_color.clicked.connect(lambda: self._pick_color("stroke"))
        
        grid.addWidget(self.chk_stroke, 3, 0)
        grid.addWidget(self.spn_stroke, 3, 1)
        grid.addWidget(self._create_label("Str Color:"), 3, 2)
        grid.addWidget(self.btn_stroke_color, 3, 3)

        self.layout.addWidget(group)

    # --- LOGIC METHODS ---
    def _pick_color(self, target):
        c = QColorDialog.getColor()
        if c.isValid():
            hex_c = c.name()
            style_sheet = f"background-color: {hex_c}; border: 1px solid #5c6370; border-radius: 2px;"
            
            if target == "text":
                self.text_color_hex = hex_c
                self.btn_text_color.setStyleSheet(style_sheet)
            elif target == "bg":
                self.bg_color_hex = hex_c
                self.btn_bg_color.setStyleSheet(style_sheet)
            elif target == "stroke":
                self.stroke_color_hex = hex_c
                self.btn_stroke_color.setStyleSheet(style_sheet)
            
            self._emit_style_update()

    def _emit_generate(self):
        data = {
            "language": self.combo_lang.currentText(),
            "preset": self.combo_preset.currentText(),
            "active": self.chk_active.isChecked(),
            "api_key": self.txt_api_key.text().strip()
        }
        self.sig_generate_caption.emit(data)
    
    def _connect_style_signals(self):
        # Hubungkan widget style ke fungsi emit update
        self.chk_active.toggled.connect(self._emit_style_update)
        self.combo_preset.currentTextChanged.connect(self._emit_style_update)
        self.font_combo.currentFontChanged.connect(self._emit_style_update)
        self.spn_size.valueChanged.connect(self._emit_style_update)
        self.chk_stroke.toggled.connect(self._emit_style_update)
        self.spn_stroke.valueChanged.connect(self._emit_style_update)
        
    def _emit_style_update(self):
        # Mengirim data styling realtime untuk preview
        data = {
            "active": self.chk_active.isChecked(),
            "preset": self.combo_preset.currentText(),
            "font": self.font_combo.currentFont().family(),
            "font_size": self.spn_size.value(),
            "text_color": self.text_color_hex,
            "bg_color": self.bg_color_hex,
            "stroke_on": self.chk_stroke.isChecked(),
            "stroke_width": self.spn_stroke.value(),
            "stroke_color": self.stroke_color_hex
        }
        self.sig_style_changed.emit(data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CaptionTab()
    window.resize(300, 700)
    window.show()
    sys.exit(app.exec())