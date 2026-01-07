from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget)
from PySide6.QtCore import Signal
from gui.right_panel.media_tab import MediaTab
from gui.right_panel.text_tab import TextTab
from gui.right_panel.caption_tab import CaptionTab

class SettingPanel(QWidget):
    on_setting_change = Signal(dict)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.media_tab = MediaTab()
        self.text_tab = TextTab()
        self.caption_tab = CaptionTab()
        
        self.tabs.addTab(self.media_tab, "Media/Frame")
        self.tabs.addTab(self.text_tab, "Text/Para")
        self.tabs.addTab(self.caption_tab, "Caption")
        
        self.layout.addWidget(self.tabs)
        self._connect_signals()

    def _connect_signals(self):
        # [FIX] Gunakan sinyal terpadu dari Tab, jangan connect manual per widget
        self.media_tab.sig_media_changed.connect(self._emit_media_change)
        self.text_tab.sig_text_changed.connect(self._emit_text_change)

    def _emit_media_change(self, data):
        data["type"] = "media"
        self.on_setting_change.emit(data)

    def _emit_text_change(self, data):
        data["type"] = "text"
        self.on_setting_change.emit(data)

    def set_values(self, data):
        # Kirim data ke tab yang sesuai
        # Data biasanya berisi semua field, tab akan ambil yg dia butuh
        self.media_tab.set_values(data)
        self.text_tab.set_values(data)

    def set_active_tab_by_type(self, content_type):
        if content_type == "media":
            self.tabs.setCurrentWidget(self.media_tab)
        elif content_type == "text":
            self.tabs.setCurrentWidget(self.text_tab)