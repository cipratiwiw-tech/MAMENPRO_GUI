from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
                             QLabel, QPushButton, QTabWidget, QFrame)
from PySide6.QtCore import Qt, QSize

class AudioTab(QWidget):
    def __init__(self):
        super().__init__()
        # Layout utama tanpa margin agar pas di tab
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Menggunakan Tab Internal untuk memisah Musik & SFX
        self.inner_tabs = QTabWidget()
        self.layout.addWidget(self.inner_tabs)
        
        # Tab 1: Music Library
        self.music_list = AudioListWidget("music")
        self.inner_tabs.addTab(self.music_list, "Music")
        
        # Tab 2: Sound Effects (SFX)
        self.sfx_list = AudioListWidget("sfx")
        self.inner_tabs.addTab(self.sfx_list, "SFX")

class AudioListWidget(QWidget):
    def __init__(self, category):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 5)
        
        # Header: Label & Tombol Import
        header_layout = QHBoxLayout()
        lbl_title = QLabel(f"LIBRARY {category.upper()}")
        lbl_title.setStyleSheet("font-weight: bold; color: #fe8019;")
        
        self.btn_import = QPushButton("Import File")
        self.btn_import.setFixedHeight(25)
        self.btn_import.setStyleSheet("""
            QPushButton { background-color: #3a0ca3; color: white; border: none; padding: 0 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #4361ee; }
        """)
        
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_import)
        layout.addLayout(header_layout)
        
        # List Widget untuk menampung item
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background-color: #1d2021; border: 1px solid #504945; border-radius: 4px; }
            QListWidget::item { border-bottom: 1px solid #3c3836; }
            QListWidget::item:selected { background-color: #3c3836; border: none; }
        """)
        layout.addWidget(self.list_widget)
        
        # --- ISI DUMMY DATA ---
        if category == "music":
            self._add_item("Cinematic Epic", "02:30", "#b16286")
            self._add_item("Happy Vibes", "01:45", "#d79921")
            self._add_item("Lo-Fi Study", "03:10", "#458588")
            self._add_item("Rock Energetic", "02:15", "#cc241d")
            self._add_item("Acoustic Morning", "02:50", "#98971a")
        else:
            self._add_item("Whoosh Transition", "00:02", "#689d6a")
            self._add_item("Mouse Click", "00:01", "#98971a")
            self._add_item("Explosion Big", "00:05", "#d65d0e")
            self._add_item("Typing Keyboard", "00:03", "#a89984")
            self._add_item("Camera Shutter", "00:01", "#458588")

    def _add_item(self, name, duration, color_code):
        # 1. Buat QListWidgetItem sebagai wadah
        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(QSize(0, 50)) # Tinggi baris item
        
        # 2. Buat Widget Custom untuk tampilan baris
        widget = QFrame()
        w_layout = QHBoxLayout(widget)
        w_layout.setContentsMargins(5, 5, 5, 5)
        w_layout.setSpacing(10)
        
        # Icon Bulat Warna (Visualisasi Cover Art)
        lbl_icon = QLabel()
        lbl_icon.setFixedSize(32, 32)
        lbl_icon.setStyleSheet(f"background-color: {color_code}; border-radius: 16px; border: 2px solid #504945;")
        
        # Info Text (Judul & Durasi)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        info_layout.setContentsMargins(0, 2, 0, 2)
        
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("font-weight: bold; color: #ebdbb2; font-size: 11px;")
        
        lbl_dur = QLabel(duration)
        lbl_dur.setStyleSheet("color: #a89984; font-size: 10px;")
        
        info_layout.addWidget(lbl_name)
        info_layout.addWidget(lbl_dur)
        info_layout.addStretch()
        
        # Tombol Aksi (Play & Add)
        btn_play = QPushButton("▶")
        btn_play.setFixedSize(26, 26)
        btn_play.setToolTip("Preview Audio")
        btn_play.setStyleSheet("""
            QPushButton { background-color: #3c3836; color: #ebdbb2; border: 1px solid #504945; border-radius: 13px; }
            QPushButton:hover { background-color: #ebdbb2; color: #282828; }
        """)
        
        btn_add = QPushButton("+")
        btn_add.setFixedSize(26, 26)
        btn_add.setToolTip("Tambahkan ke Timeline")
        btn_add.setStyleSheet("""
            QPushButton { background-color: #3c3836; color: #b8bb26; border: 1px solid #504945; border-radius: 13px; font-weight: bold; }
            QPushButton:hover { background-color: #b8bb26; color: #282828; border-color: #b8bb26; }
        """)
        btn_add.clicked.connect(lambda: print(f"Menambahkan audio: {name}"))
        
        # Masukkan ke layout
        w_layout.addWidget(lbl_icon)
        w_layout.addLayout(info_layout)
        w_layout.addStretch()
        w_layout.addWidget(btn_play)
        w_layout.addWidget(btn_add)
        
        # 3. Set Widget ke Item
        self.list_widget.setItemWidget(item, widget)