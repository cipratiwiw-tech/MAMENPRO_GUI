from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, 
                             QLabel, QComboBox, QLineEdit, QPushButton, QFileDialog, QGridLayout)
from PySide6.QtCore import Qt

class RenderTab(QWidget):
    def __init__(self):
        super().__init__()
        # Background utama gelap
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        
        group = QGroupBox("EXPORT SETTINGS")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #98c379; margin-top: 6px; color: #98c379; }")
        
        vbox = QVBoxLayout(group)
        vbox.setSpacing(12)
        vbox.setContentsMargins(10, 15, 10, 10)
        
        # 1. Quality Selection
        lbl_quality = QLabel("Resolution / Quality")
        lbl_quality.setStyleSheet("color: #abb2bf; font-size: 11px; font-weight: bold;")
        
        self.combo_quality = QComboBox()
        self.combo_quality.addItems(["480p (Fast)", "720p (HD)", "1080p (Full HD)", "4K (Ultra)"])
        self.combo_quality.setCurrentIndex(2) # Default 1080p
        self.combo_quality.setStyleSheet("""
            QComboBox { background-color: #2b2b2b; color: #dcdcdc; border: 1px solid #3e4451; padding: 4px; border-radius: 2px; }
            QComboBox::drop-down { border: none; }
        """)
        
        vbox.addWidget(lbl_quality)
        vbox.addWidget(self.combo_quality)
        
        # 2. Output Folder Section
        lbl_folder = QLabel("Output Destination")
        lbl_folder.setStyleSheet("color: #abb2bf; font-size: 11px; font-weight: bold;")
        vbox.addWidget(lbl_folder)
        
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(5)
        
        # Kolom Path
        self.txt_folder = QLineEdit()
        self.txt_folder.setPlaceholderText("Select output folder...")
        self.txt_folder.setReadOnly(True)
        self.txt_folder.setStyleSheet("background-color: #1e1e1e; color: #98c379; border: 1px solid #3e4451; font-family: Consolas; font-size: 11px; border-radius: 2px;")
        
        # Tombol Pilih Folder (...)
        self.btn_browse = QPushButton("...")
        self.btn_browse.setToolTip("Browse Folder")
        self.btn_browse.setFixedWidth(35)
        self.btn_browse.setCursor(Qt.PointingHandCursor)
        self.btn_browse.setStyleSheet("background-color: #3e4451; color: white; border-radius: 2px;")
        self.btn_browse.clicked.connect(self.on_browse_clicked)
        
        # Tombol Buka Folder (📂)
        self.btn_open_folder = QPushButton("📂")
        self.btn_open_folder.setToolTip("Open in Explorer")
        self.btn_open_folder.setFixedWidth(35)
        self.btn_open_folder.setCursor(Qt.PointingHandCursor)
        self.btn_open_folder.setStyleSheet("background-color: #d19a66; color: #282c34; border-radius: 2px;")
        
        folder_layout.addWidget(self.txt_folder)
        folder_layout.addWidget(self.btn_browse)
        folder_layout.addWidget(self.btn_open_folder)
        
        vbox.addLayout(folder_layout)
        
        # 3. Action Buttons (Render & Stop)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(5)
        
        self.btn_render = QPushButton("🎬 RENDER VIDEO")
        self.btn_render.setFixedHeight(40)
        self.btn_render.setCursor(Qt.PointingHandCursor)
        self.btn_render.setStyleSheet("""
            QPushButton { background-color: #2a9d8f; color: white; font-weight: bold; border-radius: 3px; border: none; }
            QPushButton:hover { background-color: #2ec4b6; }
            QPushButton:pressed { background-color: #264653; }
        """)
        
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setFixedHeight(40)
        self.btn_stop.setFixedWidth(60)
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setStyleSheet("""
            QPushButton { background-color: #e63946; color: white; font-weight: bold; border-radius: 3px; border: none; }
            QPushButton:disabled { background-color: #4a2c2c; color: #7a7a7a; }
        """)
        self.btn_stop.setEnabled(False) 
        
        action_layout.addWidget(self.btn_render)
        action_layout.addWidget(self.btn_stop)
        
        vbox.addStretch() # Push content to top
        vbox.addLayout(action_layout)
        
        layout.addWidget(group)

    def on_browse_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.txt_folder.setText(folder)