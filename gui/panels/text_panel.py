# gui/panels/text_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
from PySide6.QtCore import Signal

# Import Sub-Komponen
from gui.panels.text_parts.content_section import ContentSection
from gui.panels.text_parts.font_section import FontSection
from gui.panels.text_parts.style_section import StyleSection

class TextPanel(QWidget):
    # Sinyal Gabungan ke Luar (Binder/Controller)
    sig_property_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        
        self._init_ui()
        self._connect_internal_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Scroll Area agar tidak mentok jika panel banyak
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(20)

        # 1. Content
        self.content_sec = ContentSection()
        self.layout.addWidget(self.content_sec)
        
        self.layout.addWidget(self._h_line())

        # 2. Font
        self.font_sec = FontSection()
        self.layout.addWidget(self.font_sec)

        self.layout.addWidget(self._h_line())

        # 3. Style
        self.style_sec = StyleSection()
        self.layout.addWidget(self.style_sec)

        self.layout.addStretch()
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _h_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #3e4451;")
        return line

    def _connect_internal_signals(self):
        # Tangkap sinyal anak-anak, teruskan ke Binder
        self.content_sec.sig_content_changed.connect(self.sig_property_changed)
        self.font_sec.sig_font_changed.connect(self.sig_property_changed)
        self.style_sec.sig_style_changed.connect(self.sig_property_changed)

    # --- API UNTUK BINDER (Terima Data) ---
    def set_values(self, props: dict):
        """Mendistribusikan data ke sub-panel"""
        self.content_sec.set_values(props)
        self.font_sec.set_values(props)
        self.style_sec.set_values(props)