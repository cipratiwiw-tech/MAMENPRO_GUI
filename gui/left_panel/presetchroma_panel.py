from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt

class PresetChromaPanel(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setStyleSheet("border: none;") 
        
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)
        
        # 1. Header (Tombol Import & Save)
        self._init_header()
        
        # 2. Grid Thumbnail (Library)
        self._init_grid()
        
        self.main_layout.addStretch()
        self.setWidget(container)

    def _init_header(self):
        """Header berisi tombol Import File Baru & Simpan Settingan Layer Aktif"""
        header_group = QWidget()
        header_layout = QVBoxLayout(header_group)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        lbl_info = QLabel("CHROMA LIBRARY")
        lbl_info.setStyleSheet("color: #ebdbb2; font-weight: bold; font-size: 14px;")
        
        # Tombol Import File (Raw)
        self.btn_import = QPushButton(" + Import File")
        self.btn_import.setFixedHeight(35)
        self.btn_import.setStyleSheet("""
            QPushButton {
                background-color: #3a0ca3; color: white; font-weight: bold; border-radius: 4px;
            }
            QPushButton:hover { background-color: #4361ee; }
        """)
        self.btn_import.clicked.connect(lambda: print("Import File Clicked"))
        
        # Tombol Save Current Selection (Simpan settingan layer yg diedit)
        self.btn_save_selection = QPushButton(" 💾 Save Selected Layer as Preset")
        self.btn_save_selection.setFixedHeight(35)
        self.btn_save_selection.setStyleSheet("""
            QPushButton {
                background-color: #d65d0e; color: #fbf1c7; font-weight: bold; border-radius: 4px;
            }
            QPushButton:hover { background-color: #fe8019; color: #282828; }
        """)
        self.btn_save_selection.clicked.connect(self.on_save_clicked)
        
        header_layout.addWidget(lbl_info)
        
        # Baris Tombol
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_import)
        btn_row.addWidget(self.btn_save_selection)
        header_layout.addLayout(btn_row)
        
        self.main_layout.addWidget(header_group)

    def _init_grid(self):
        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(10)
        self.grid.setContentsMargins(0, 0, 0, 0)
        
        # Dummy Data Library
        self._add_card(0, "Fire Explosion", "#e74c3c")
        self._add_card(1, "Smoke Effect", "#95a5a6")
        self._add_card(2, "Dinosaur Run", "#2ecc71")
        self._add_card(3, "Meme Shia", "#f1c40f")
        self._add_card(4, "Rain Overlay", "#3498db")
        
        self.main_layout.addWidget(self.grid_container)

    def _add_card(self, index, name, color_code):
        card = QFrame()
        card.setFixedSize(135, 160) # Tinggi sedikit ditambah untuk tombol hapus
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #3c3836; 
                border: 1px solid #504945; 
                border-radius: 8px;
            }}
            QFrame:hover {{
                border: 1px solid #fe8019;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # 1. Thumbnail
        thumb = QLabel()
        thumb.setStyleSheet(f"background-color: {color_code}; border-radius: 4px;")
        thumb.setFixedSize(123, 75)
        thumb.setAlignment(Qt.AlignCenter)
        thumb.setText("GS")
        
        # 2. Nama Item
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("color: #ebdbb2; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        lbl_name.setAlignment(Qt.AlignCenter)
        lbl_name.setFixedHeight(20)
        
        # 3. Container Tombol (Load & Delete)
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 5, 0, 0)
        action_layout.setSpacing(4)
        
        # Tombol Load (Hijau/Standar)
        btn_load = QPushButton("Load")
        btn_load.setCursor(Qt.PointingHandCursor)
        btn_load.setFixedHeight(24)
        btn_load.setStyleSheet("""
            QPushButton {
                background-color: #504945; border: none; color: #fbf1c7; font-size: 10px; border-radius: 3px;
            }
            QPushButton:hover { background-color: #689d6a; color: white; }
        """)
        btn_load.clicked.connect(lambda: print(f"Loading Preset: {name}"))
        
        # Tombol Delete (Merah Kecil)
        btn_del = QPushButton("X")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setFixedSize(24, 24)
        btn_del.setStyleSheet("""
            QPushButton {
                background-color: #282828; border: 1px solid #cc241d; color: #cc241d; font-weight: bold; border-radius: 3px;
            }
            QPushButton:hover { background-color: #cc241d; color: white; }
        """)
        # Simulasi Hapus
        btn_del.clicked.connect(lambda: self.on_delete_clicked(card, name))
        
        action_layout.addWidget(btn_load)
        action_layout.addWidget(btn_del)
        
        layout.addWidget(thumb)
        layout.addWidget(lbl_name)
        layout.addLayout(action_layout)
        
        # Posisi Grid
        row = index // 2
        col = index % 2
        self.grid.addWidget(card, row, col)

    def on_save_clicked(self):
        print("Menyimpan settingan Chroma layer terpilih ke library...")
        # Di sini nanti logika mengambil data dari MediaTab/Engine
        # Lalu self._add_card(...) baru

    def on_delete_clicked(self, card_widget, name):
        # Konfirmasi Hapus (Opsional)
        print(f"Menghapus preset: {name}")
        card_widget.deleteLater() # Menghapus widget kartu dari UI