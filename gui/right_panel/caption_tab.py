from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                             QLabel, QSpinBox, QPushButton, QComboBox, 
                             QTextEdit, QScrollArea, QCheckBox, QHBoxLayout, 
                             QFontComboBox, QFrame, QLineEdit) # <--- Ditambah QLineEdit
from PySide6.QtCore import Qt

from PySide6.QtCore import Signal


class CaptionTab(QScrollArea):
    sig_generate_caption = Signal(dict) # Kirim opsi generate caption
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(15)
        
        # 1. Panel Auto Caption
        self._init_generation()
        
        # 2. Toggle Aktivasi Dummy
        self._init_activation_toggle()
        
        # 3. Panel Gaya/Styling (SUDAH DITAMBAH STROKE COLOR)
        self._init_style()
        
        # 4. Dropdown Preset
        self._init_preset_section()
        
        # 5. Editor Manual
        self._init_editor()
        
        self.layout.addStretch()
        self.setWidget(container)

    def _init_generation(self):
        group = QGroupBox("AUTO CAPTION")
        grid = QGridLayout(group)
        
        # --- [BARU] AssemblyAI Key Input (Row 0) ---
        row_api = QHBoxLayout()
        row_api.setContentsMargins(0, 0, 0, 0)
        
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setPlaceholderText("Paste AssemblyAI API Key...")
        self.txt_api_key.setEchoMode(QLineEdit.Password) # Password mode agar key tersembunyi
        self.txt_api_key.setStyleSheet("background-color: #1d2021; color: #ebdbb2; border: 1px solid #504945; border-radius: 4px;")
        
        self.btn_save_key = QPushButton("Save")
        self.btn_save_key.setFixedWidth(50)
        self.btn_save_key.setStyleSheet("background-color: #504945; color: #fbf1c7; border: none; border-radius: 4px; font-weight: bold;")
        
        row_api.addWidget(QLabel("AssemblyAI Key:"))
        row_api.addWidget(self.txt_api_key)
        row_api.addWidget(self.btn_save_key)
        
        # Masukkan baris API Key ke Grid paling atas (Row 0, Span 2 kolom)
        grid.addLayout(row_api, 0, 0, 1, 2)

        # --- [LAMA] Bahasa (Digeser ke Row 1) ---
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Indonesia", "English",])
        
        grid.addWidget(QLabel("Bahasa:"), 1, 0)
        grid.addWidget(self.combo_lang, 1, 1)
        
        # --- [LAMA] Tombol Generate (Digeser ke Row 2) ---
        self.btn_generate = QPushButton("⚡ Generate Auto Caption")
        self.btn_generate.setStyleSheet("background-color: #d65d0e; color: #fbf1c7; border: none; font-weight: bold;")
        self.btn_generate.setFixedHeight(35)
        
        self.btn_generate.clicked.connect(self._emit_generate)

        
        grid.addWidget(self.btn_generate, 2, 0, 1, 2)
        
        self.layout.addWidget(group)
    def _emit_generate(self):
        data = {
            "language": self.combo_lang.currentText(),
            "preset": self.combo_preset.currentText(),
            "active": self.chk_active.isChecked(),
            "api_key": self.txt_api_key.text().strip()
        }
        self.sig_generate_caption.emit(data)

    def _init_activation_toggle(self):
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #3c3836; 
                border: 1px solid #504945; 
                border-radius: 6px;
            }
        """)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 8)
        
        self.chk_active = QCheckBox("Aktifkan Preview Dummy Caption")
        self.chk_active.setToolTip("Jika ON: Menampilkan contoh caption dan akan dirender otomatis.")
        self.chk_active.setStyleSheet("font-weight: bold; color: #fe8019; font-size: 13px; border: none;")
        
        layout.addWidget(self.chk_active)
        self.layout.addWidget(container)

    def _init_style(self):
        group = QGroupBox("GAYA CAPTION")
        grid = QGridLayout(group)
        grid.setVerticalSpacing(10)
        
        # Font & Ukuran
        self.font_combo = QFontComboBox()
        
        self.spn_size = QSpinBox()
        self.spn_size.setRange(10, 200)
        self.spn_size.setValue(24)
        self.spn_size.setSuffix(" px")
        
        # Tombol Warna Dasar
        self.btn_text_color = QPushButton("Warna Teks")
        self.btn_bg_color = QPushButton("Warna Background")
        
        # --- STROKE SECTION (BARU) ---
        self.chk_stroke = QCheckBox("Stroke")
        
        self.spn_stroke_width = QSpinBox()
        self.spn_stroke_width.setRange(0, 20)
        self.spn_stroke_width.setPrefix("Tebal: ")
        
        self.btn_stroke_color = QPushButton("Warna Stroke")
        
        # Layouting Grid
        # Baris 0: Font
        grid.addWidget(QLabel("Font:"), 0, 0)
        grid.addWidget(self.font_combo, 0, 1)
        
        # Baris 1: Ukuran
        grid.addWidget(QLabel("Ukuran:"), 1, 0)
        grid.addWidget(self.spn_size, 1, 1)
        
        # Baris 2: Warna Teks & BG
        row_color = QHBoxLayout()
        row_color.addWidget(self.btn_text_color)
        row_color.addWidget(self.btn_bg_color)
        grid.addLayout(row_color, 2, 0, 1, 2)
        
        # Baris 3: Konfigurasi Stroke Lengkap
        row_stroke = QHBoxLayout()
        row_stroke.addWidget(self.chk_stroke)
        row_stroke.addWidget(self.spn_stroke_width)
        row_stroke.addWidget(self.btn_stroke_color)
        grid.addLayout(row_stroke, 3, 0, 1, 2)
        
        self.layout.addWidget(group)

    def _init_preset_section(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 5, 0, 0)
        
        layout.addWidget(QLabel("Pilih Preset Style:"))
        
        self.combo_preset = QComboBox()
        self.combo_preset.addItems([
            "Custom (Manual)", 
            "Karaoke Highlight (Word-by-word)", 
            "Netflix Standard", 
            "Youtube Shorts (Yellow Bold)", 
            "Cinematic Minimal"
        ])
        
        layout.addWidget(self.combo_preset)
        self.layout.addWidget(container)

    def _init_editor(self):
        group = QGroupBox("EDITOR SUBTITLE")
        layout = QVBoxLayout(group)
        
        self.txt_editor = QTextEdit()
        self.txt_editor.setPlaceholderText("00:00 - Halo semuanya...\n00:05 - Selamat datang di Mamen Pro...")
        self.txt_editor.setMinimumHeight(150)
        self.txt_editor.setStyleSheet("background-color: #1d2021; border: 1px solid #504945; font-family: Consolas; color: #ebdbb2;")
        
        layout.addWidget(self.txt_editor)
        
        btn_layout = QGridLayout()
        self.btn_import = QPushButton("Import .SRT")
        self.btn_export = QPushButton("Export .SRT")
        
        btn_layout.addWidget(self.btn_import, 0, 0)
        btn_layout.addWidget(self.btn_export, 0, 1)
        
        layout.addLayout(btn_layout)
        self.layout.addWidget(group)
        
# ... (kode class PreviewPanel di atas) ...

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    # --- SIMULASI UKURAN ---
    MAIN_WINDOW_W = 1920  # Anggap layar Full HD
    MAIN_WINDOW_H = 1000  # Tinggi layar dikurangi taskbar
    
    # Hitung jatah panel tengah (3/5 dari lebar total)
    my_width = int(MAIN_WINDOW_W * (1/6))
    my_height = MAIN_WINDOW_H * (3/5)

    window = QWidget()
    layout = QVBoxLayout(window)
    layout.setContentsMargins(0,0,0,0) # Hilangkan margin biar akurat
    
    panel = CaptionTab()
    layout.addWidget(panel)
    
    # Terapkan hasil hitungan
    window.resize(my_width, my_height)
    
    window.setWindowTitle(f"Testing Preview Panel ({my_width}x{my_height})")
    window.show()
    
    sys.exit(app.exec())