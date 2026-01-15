from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, 
                             QLabel, QComboBox, QLineEdit, QPushButton, QFileDialog, QStyle)
from PySide6.QtCore import Qt

class RenderTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        group = QGroupBox("EKSPOR VIDEO")
        vbox = QVBoxLayout(group)
        vbox.setSpacing(10)
        
        # 1. Quality Selection
        self.combo_quality = QComboBox()
        self.combo_quality.addItems(["480p (Cepat)", "720p (HD)", "1080p (Full HD)", "4K (Ultra)"])
        self.combo_quality.setCurrentIndex(2) # Default 1080p
        
        vbox.addWidget(QLabel("Kualitas Render:"))
        vbox.addWidget(self.combo_quality)
        
        # 2. Output Folder Section
        vbox.addWidget(QLabel("Folder Penyimpanan:"))
        
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(5)
        
        # Kolom Path (Read Only agar user pakai tombol)
        self.txt_folder = QLineEdit()
        self.txt_folder.setPlaceholderText("Pilih folder tujuan...")
        self.txt_folder.setReadOnly(True)
        self.txt_folder.setStyleSheet("background-color: #2d3436; color: #dfe6e9; border: 1px solid #636e72;")
        
        # Tombol Pilih Folder (...)
        self.btn_browse = QPushButton("...")
        self.btn_browse.setToolTip("Pilih Folder Tujuan")
        self.btn_browse.setFixedWidth(40)
        self.btn_browse.setStyleSheet("background-color: #0984e3; color: white; font-weight: bold;")
        self.btn_browse.clicked.connect(self.on_browse_clicked)
        
        # Tombol Buka Folder (📂)
        self.btn_open_folder = QPushButton("📂")
        self.btn_open_folder.setToolTip("Buka Folder di Explorer")
        self.btn_open_folder.setFixedWidth(40)
        self.btn_open_folder.setStyleSheet("background-color: #e17055; color: white; font-weight: bold;")
        # Logika buka folder akan di-handle di Controller, tapi kita bisa pasang signal di sini atau connect nanti
        
        folder_layout.addWidget(self.txt_folder)
        folder_layout.addWidget(self.btn_browse)
        folder_layout.addWidget(self.btn_open_folder)
        
        vbox.addLayout(folder_layout)
        
        # 3. Action Buttons (Render & Stop)
        action_layout = QHBoxLayout()
        
        self.btn_render = QPushButton("🎬 MULAI RENDER")
        self.btn_render.setFixedHeight(45)
        self.btn_render.setStyleSheet("background-color: #2a9d8f; color: white; font-size: 14px; font-weight: bold;")
        
        self.btn_stop = QPushButton("🛑 STOP")
        self.btn_stop.setFixedHeight(45)
        self.btn_stop.setStyleSheet("background-color: #e63946; color: white; font-size: 14px; font-weight: bold;")
        self.btn_stop.setEnabled(False) 
        
        action_layout.addWidget(self.btn_render, stretch=3)
        action_layout.addWidget(self.btn_stop, stretch=1)
        
        vbox.addStretch()
        vbox.addLayout(action_layout)
        
        layout.addWidget(group)

    def on_browse_clicked(self):
        # Dialog pilih FOLDER (Directory), bukan File
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Output")
        if folder:
            self.txt_folder.setText(folder)