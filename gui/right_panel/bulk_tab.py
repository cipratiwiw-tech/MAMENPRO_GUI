# Simpan file ini di: gui/right_panel/bulk_tab.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, 
                             QPushButton, QTextEdit, QScrollArea, QCheckBox, 
                             QGridLayout, QComboBox, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, Signal

class BulkTab(QScrollArea):
    # Sinyal untuk mengirim data bulk ke Controller
    sig_start_bulk = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        
        # Container utama dengan style gelap sesuai tema aplikasi
        container = QWidget()
        container.setStyleSheet("background-color: #23272e;") 
        
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(8, 8, 8, 8)
        
        self._init_input_section()
        self._init_mapping_section()
        self._init_action_section()
        
        self.layout.addStretch()
        self.setWidget(container)

    def _create_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #abb2bf; font-size: 11px; font-weight: bold;") 
        return lbl

    def _init_input_section(self):
        # Group Box untuk Input Data
        group = QGroupBox("DATA SOURCE (CSV/TEXT)")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #d19a66; margin-top: 6px; color: #d19a66; }")
        
        vbox = QVBoxLayout(group)
        vbox.setSpacing(8)
        vbox.setContentsMargins(10, 15, 10, 10)
        
        # Instruksi
        lbl_info = QLabel("Format: Baris baru = Video baru")
        lbl_info.setStyleSheet("color: #5c6370; font-size: 10px; font-style: italic;")
        vbox.addWidget(lbl_info)

        # Text Area Input
        self.txt_data = QTextEdit()
        self.txt_data.setPlaceholderText("Contoh:\nKata Mutiara 1\nKata Mutiara 2\nKata Mutiara 3...")
        self.txt_data.setMinimumHeight(120)
        self.txt_data.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b; color: #98c379; 
                border: 1px solid #3e4451; border-radius: 3px;
                font-family: Consolas; font-size: 11px;
            }
            QTextEdit:focus { border: 1px solid #d19a66; }
        """)
        vbox.addWidget(self.txt_data)
        
        # Tombol Import & Clear
        btn_layout = QGridLayout()
        self.btn_import_csv = QPushButton("Import CSV")
        self.btn_clear = QPushButton("Clear")
        
        for btn in [self.btn_import_csv, self.btn_clear]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("background-color: #3e4451; color: #dcdcdc; border-radius: 2px; padding: 4px;")
            
        btn_layout.addWidget(self.btn_import_csv, 0, 0)
        btn_layout.addWidget(self.btn_clear, 0, 1)
        vbox.addLayout(btn_layout)
        
        self.layout.addWidget(group)

    def _init_mapping_section(self):
        # Group Box untuk Mapping
        group = QGroupBox("MAPPING TARGET")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #56b6c2; margin-top: 6px; color: #56b6c2; }")
        
        vbox = QVBoxLayout(group)
        vbox.setSpacing(10)
        vbox.setContentsMargins(10, 15, 10, 10)
        
        # Target Layer Selector
        self.combo_target_layer = QComboBox()
        self.combo_target_layer.addItems(["-- Pilih Layer Teks --"])
        self.combo_target_layer.setStyleSheet("""
            QComboBox { background-color: #2b2b2b; color: #dcdcdc; border: 1px solid #3e4451; padding: 4px; }
            QComboBox::drop-down { border: none; }
        """)
        
        vbox.addWidget(self._create_label("Apply Text To:"))
        vbox.addWidget(self.combo_target_layer)
        
        # Random Background Option
        self.chk_random_bg = QCheckBox("Randomize Background")
        self.chk_random_bg.setStyleSheet("color: #abb2bf;")
        vbox.addWidget(self.chk_random_bg)
        
        self.layout.addWidget(group)

    def _init_action_section(self):
        group = QGroupBox("GENERATION")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #c678dd; margin-top: 6px; color: #c678dd; }")
        
        vbox = QVBoxLayout(group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #3e4451; border-radius: 2px; text-align: center; color: white; }
            QProgressBar::chunk { background-color: #98c379; }
        """)
        
        self.btn_generate = QPushButton("🚀 START BULK RENDER")
        self.btn_generate.setFixedHeight(40)
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.setStyleSheet("""
            QPushButton { 
                background-color: #98c379; color: #282c34; 
                font-weight: bold; border-radius: 3px; font-size: 12px;
            }
            QPushButton:hover { background-color: #b5e890; }
            QPushButton:pressed { background-color: #7a9e60; }
        """)
        self.btn_generate.clicked.connect(self._on_generate_clicked)
        
        vbox.addWidget(self.progress_bar)
        vbox.addWidget(self.btn_generate)
        
        self.layout.addWidget(group)

    def update_layer_list(self, layer_names):
        """Dipanggil dari Controller untuk update list layer teks yang tersedia"""
        current = self.combo_target_layer.currentText()
        self.combo_target_layer.clear()
        self.combo_target_layer.addItem("-- Pilih Layer Teks --")
        self.combo_target_layer.addItems(layer_names)
        
        # Restore selection if possible
        idx = self.combo_target_layer.findText(current)
        if idx >= 0:
            self.combo_target_layer.setCurrentIndex(idx)

    def _on_generate_clicked(self):
        data_text = self.txt_data.toPlainText().strip()
        if not data_text:
            QMessageBox.warning(self, "Data Kosong", "Silakan masukkan teks data terlebih dahulu.")
            return
            
        target_layer = self.combo_target_layer.currentText()
        if target_layer.startswith("--"):
            QMessageBox.warning(self, "Target Kosong", "Silakan pilih Layer Teks target.")
            return

        # Kirim data ke Controller untuk diproses
        payload = {
            "raw_data": data_text.split('\n'),
            "target_layer": target_layer,
            "random_bg": self.chk_random_bg.isChecked()
        }
        self.sig_start_bulk.emit(payload)