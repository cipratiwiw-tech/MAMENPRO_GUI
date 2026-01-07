from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, 
                             QLabel, QComboBox, QLineEdit, QPushButton)

class RenderTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        group = QGroupBox("EKSPOR VIDEO")
        vbox = QVBoxLayout(group)
        
        # Quality
        self.combo_quality = QComboBox()
        self.combo_quality.addItems(["480p (Cepat)", "720p (HD)", "1080p (Full HD)", "4K (Ultra)"])
        vbox.addWidget(QLabel("Kualitas Render:"))
        vbox.addWidget(self.combo_quality)
        
        # Path
        hbox = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("C:/Output/Video.mp4")
        self.btn_browse = QPushButton("...")
        self.btn_browse.setFixedWidth(40)
        hbox.addWidget(self.txt_path)
        hbox.addWidget(self.btn_browse)
        vbox.addLayout(hbox)
        
        # --- BAGIAN TOMBOL ACTION (MODIFIKASI DI SINI) ---
        
        # Buat layout horizontal agar tombol bersebelahan
        action_layout = QHBoxLayout()
        
        # 1. Tombol Mulai (Warna Hijau Teal)
        self.btn_render = QPushButton("🎬 MULAI RENDER")
        self.btn_render.setFixedHeight(45)
        self.btn_render.setStyleSheet("background-color: #2a9d8f; color: white; font-size: 14px; font-weight: bold;")
        
        # 2. Tombol Stop (Warna Merah) - Tambahan Baru
        self.btn_stop = QPushButton("🛑 STOP")
        self.btn_stop.setFixedHeight(45)
        self.btn_stop.setStyleSheet("background-color: #e63946; color: white; font-size: 14px; font-weight: bold;")
        self.btn_stop.setEnabled(False) # Default mati, nyala pas lagi render
        
        # Masukkan kedua tombol ke layout horizontal
        action_layout.addWidget(self.btn_render, stretch=3) # Lebih lebar dikit
        action_layout.addWidget(self.btn_stop, stretch=1)
        
        vbox.addStretch()
        vbox.addLayout(action_layout) # Masukkan layout tombol ke layout utama
        
        layout.addWidget(group)