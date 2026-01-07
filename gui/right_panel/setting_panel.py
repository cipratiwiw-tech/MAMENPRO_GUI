from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget)
from PySide6.QtCore import Qt, Signal

# Import Modul
from gui.right_panel.media_tab import MediaTab
from gui.right_panel.text_tab import TextTab
from gui.right_panel.caption_tab import CaptionTab

class SettingPanel(QWidget):
    on_setting_change = Signal(dict) 

    def __init__(self):
        super().__init__()
        self.setFixedWidth(340)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.media_tab = MediaTab()
        self.text_tab = TextTab()
        self.caption_tab = CaptionTab()
        
        self.tabs.addTab(self.media_tab, "Media")
        self.tabs.addTab(self.text_tab, "Teks")
        self.tabs.addTab(self.caption_tab, "Caption")
        
        self.main_layout.addWidget(self.tabs)

        self._connect_signals()

    def _connect_signals(self):
        # --- 1. MEDIA TAB SIGNALS ---
        # Konten (Clip) - Mempengaruhi ISI Frame
        self.media_tab.spn_x.valueChanged.connect(self._emit_media_change)
        self.media_tab.spn_y.valueChanged.connect(self._emit_media_change)
        self.media_tab.spn_scale.valueChanged.connect(self._emit_media_change)
        self.media_tab.spn_rot.valueChanged.connect(self._emit_media_change)
        self.media_tab.spn_opacity.valueChanged.connect(self._emit_media_change)
        
        # Smart Frame (Crop)
        self.media_tab.spn_sf_l.valueChanged.connect(self._emit_media_change)
        self.media_tab.spn_sf_r.valueChanged.connect(self._emit_media_change)

        # Frame (Wadah) - Mempengaruhi BENTUK Frame
        self.media_tab.spn_frame_w.valueChanged.connect(self._emit_media_change)
        self.media_tab.spn_frame_h.valueChanged.connect(self._emit_media_change)
        self.media_tab.spn_frame_rot.valueChanged.connect(self._emit_media_change)
        
        # Lock
        self.media_tab.chk_lock_frame.toggled.connect(self._emit_media_change)

        # --- 2. TEXT TAB SIGNALS ---
        # Asumsi TextTab memiliki signal sig_text_changed(dict)
        self.text_tab.sig_text_changed.connect(self._emit_text_change)

    def _emit_media_change(self):
        """Mengambil semua nilai dari tab Media dan mengirimnya sebagai signal"""
        data = {
            "type": "media", # Flag tipe
            "x": self.media_tab.spn_x.value(),
            "y": self.media_tab.spn_y.value(),
            "scale": self.media_tab.spn_scale.value(),
            "rotation": self.media_tab.spn_rot.value(), # Rotasi Clip
            "opacity": self.media_tab.spn_opacity.value(),
            "sf_l": self.media_tab.spn_sf_l.value(),
            "sf_r": self.media_tab.spn_sf_r.value(),
            
            "frame_w": self.media_tab.spn_frame_w.value(),
            "frame_h": self.media_tab.spn_frame_h.value(),
            "frame_rot": self.media_tab.spn_frame_rot.value(), # Rotasi Frame
            "lock": self.media_tab.chk_lock_frame.isChecked()
        }
        self.on_setting_change.emit(data)

    def _emit_text_change(self, text_data):
        """Meneruskan perubahan dari tab Teks"""
        # Tambahkan flag tipe agar Controller tau ini update teks
        text_data["type"] = "text"
        self.on_setting_change.emit(text_data)

    def set_values(self, data):
        """Menerima data dari Main Window (saat seleksi berubah) dan update UI"""
        # Block sinyal utama panel
        self.blockSignals(True)
        
        # --- UPDATE MEDIA TAB ---
        # Block signals UI elements Media (agar tidak memicu update loop)
        self.media_tab.spn_x.blockSignals(True)
        self.media_tab.spn_y.blockSignals(True)
        self.media_tab.spn_scale.blockSignals(True)
        self.media_tab.spn_rot.blockSignals(True)
        self.media_tab.spn_opacity.blockSignals(True)
        self.media_tab.spn_sf_l.blockSignals(True)
        self.media_tab.spn_sf_r.blockSignals(True)
        
        self.media_tab.spn_frame_w.blockSignals(True)
        self.media_tab.spn_frame_h.blockSignals(True)
        self.media_tab.spn_frame_rot.blockSignals(True)
        self.media_tab.chk_lock_frame.blockSignals(True)

        # Set Nilai (Gunakan .get() agar aman jika key tidak ada)
        self.media_tab.spn_x.setValue(int(data.get("x", 0)))
        self.media_tab.spn_y.setValue(int(data.get("y", 0)))
        self.media_tab.spn_scale.setValue(int(data.get("scale", 100)))
        self.media_tab.spn_rot.setValue(int(data.get("rot", 0)))
        self.media_tab.spn_opacity.setValue(int(data.get("opacity", 100)))
        self.media_tab.spn_sf_l.setValue(int(data.get("sf_l", 0)))
        self.media_tab.spn_sf_r.setValue(int(data.get("sf_r", 0)))
        
        # Frame Properties
        self.media_tab.spn_frame_w.setValue(int(data.get("frame_w", 540)))
        self.media_tab.spn_frame_h.setValue(int(data.get("frame_h", 960)))
        self.media_tab.spn_frame_rot.setValue(int(data.get("frame_rot", 0)))
        
        # Handle Lock State
        is_locked = bool(data.get("lock", False))
        self.media_tab.chk_lock_frame.setChecked(is_locked)
        self._update_lock_state(is_locked)

        # Unblock signals Media
        self.media_tab.spn_x.blockSignals(False)
        self.media_tab.spn_y.blockSignals(False)
        self.media_tab.spn_scale.blockSignals(False)
        self.media_tab.spn_rot.blockSignals(False)
        self.media_tab.spn_opacity.blockSignals(False)
        self.media_tab.spn_sf_l.blockSignals(False)
        self.media_tab.spn_sf_r.blockSignals(False)
        
        self.media_tab.spn_frame_w.blockSignals(False)
        self.media_tab.spn_frame_h.blockSignals(False)
        self.media_tab.spn_frame_rot.blockSignals(False)
        self.media_tab.chk_lock_frame.blockSignals(False)
        
        # --- UPDATE TEXT TAB ---
        # Jika konten yang dipilih adalah teks, update tab teks juga
        if data.get("content_type") == "text":
            self.text_tab.set_values(data)

        # Unblock sinyal utama panel
        self.blockSignals(False)

    def _update_lock_state(self, is_locked):
        """Mematikan input jika terkunci"""
        enabled = not is_locked
        self.media_tab.spn_x.setEnabled(enabled)
        self.media_tab.spn_y.setEnabled(enabled)
        self.media_tab.spn_frame_w.setEnabled(enabled)
        self.media_tab.spn_frame_h.setEnabled(enabled)
        self.media_tab.spn_frame_rot.setEnabled(enabled)

    def set_active_tab_by_type(self, content_type):
        """Berpindah tab otomatis berdasarkan tipe konten frame"""
        if content_type == "text":
            self.tabs.setCurrentIndex(1) # Pindah ke Tab Teks
        elif content_type == "media":
            self.tabs.setCurrentIndex(0) # Pindah ke Tab Media