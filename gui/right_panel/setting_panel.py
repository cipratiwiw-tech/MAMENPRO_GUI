from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget)
from PySide6.QtCore import Signal
from gui.panels.media_panel import MediaTab
from gui.panels.text_panel import TextTab
from gui.panels.caption_panel import CaptionTab
from gui.right_panel.bulk_tab import BulkTab

class SettingPanel(QWidget):
    on_setting_change = Signal(dict)
    sig_bulk_requested = Signal(dict)
    
    def __init__(self):
        super().__init__()
        
        # [UPGRADE] Set batas minimal dan maksimal
        # Agar panel kanan tidak pernah kurang dari 340px (mencegah clipping)
        # Dan tidak lebih dari 450px (mencegah terlalu lebar)
        self.setMinimumWidth(340)
        self.setMaximumWidth(450)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Inisialisasi Tab Widget
        self.tabs = QTabWidget()
        
        # Inisialisasi Konten Tab
        self.media_tab = MediaTab()
        self.text_tab = TextTab()
        self.caption_tab = CaptionTab()
        self.bulk_tab = BulkTab()
        
        # Menambahkan Tab ke Widget
        self.tabs.addTab(self.media_tab, "Media/Frame")
        self.tabs.addTab(self.text_tab, "Text/Para")
        self.tabs.addTab(self.caption_tab, "Caption")        
        self.tabs.addTab(self.bulk_tab, "Bulk")
        
        self.layout.addWidget(self.tabs)
        self._connect_signals()

    def _connect_signals(self):
        # [FIX] Gunakan sinyal terpadu dari Tab
        self.media_tab.sig_media_changed.connect(self._emit_media_change)
        self.text_tab.sig_text_changed.connect(self._emit_text_change)
        self.bulk_tab.sig_start_bulk.connect(self.sig_bulk_requested.emit)

    def _emit_media_change(self, data):
        """Membungkus data media dengan type tag sebelum di-emit"""
        data["type"] = "media"
        self.on_setting_change.emit(data)

    def _emit_text_change(self, data):
        """Membungkus data text dengan type tag sebelum di-emit"""
        data["type"] = "text"
        self.on_setting_change.emit(data)

    def set_values(self, data):
        """Mengirim data ke tab yang sesuai untuk update UI"""
        # Tab akan memfilter data yang relevan secara internal
        self.media_tab.set_values(data)
        self.text_tab.set_values(data)

    def set_active_tab_by_type(self, content_type):
        """
        Dipanggil dari MainController saat item di timeline/list diklik.
        Mengatur tab mana yang aktif berdasarkan tipe konten.
        """
        if content_type == "media":
            self.tabs.setCurrentWidget(self.media_tab)
            
        elif content_type == "text":
            self.tabs.setCurrentWidget(self.text_tab)
        
        # [BARU] Arahkan ke Caption Tab
        elif content_type == "caption_preview":
            self.tabs.setCurrentWidget(self.caption_tab)
            
        elif content_type == "bulk":
             self.tabs.setCurrentWidget(self.bulk_tab)