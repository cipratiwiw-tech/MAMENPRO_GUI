# [NEW FILE] gui/left_panel/assets_panel.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QGroupBox, QLabel
from PySide6.QtCore import Signal
from gui.services.media_dialog_service import MediaDialogService

class AssetsPanel(QWidget):
    # Gabungan Signal dari panel-panel sebelumnya
    sig_request_import = Signal(str, str) # type, path (Media)
    sig_set_background = Signal(str)      # path (Background)
    sig_add_text = Signal(str, int)       # content, font_size (Text)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 20, 15, 20)

        # --- JUDUL ---
        lbl_title = QLabel("QUICK ASSETS")
        lbl_title.setStyleSheet("font-weight: bold; color: #61afef; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        # --- GROUP 1: MEDIA & BG ---
        group_media = self._create_group("MEDIA FILES")
        media_layout = QVBoxLayout(group_media)
        media_layout.setSpacing(10)
        
        # Tombol Add Media
        btn_media = self._create_btn("📂 Add Media", "#3a0ca3")
        btn_media.clicked.connect(self._on_add_media)
        
        # Tombol Add Background
        btn_bg = self._create_btn("🖼️ Add Background", "#e5c07b", text_color="#282c34")
        btn_bg.setToolTip("Layer ini akan otomatis ditaruh di paling bawah.")
        btn_bg.clicked.connect(self._on_add_bg)
        
        media_layout.addWidget(btn_media)
        media_layout.addWidget(btn_bg)
        layout.addWidget(group_media)

        # --- GROUP 2: TEXT ---
        group_text = self._create_group("TYPOGRAPHY")
        text_layout = QVBoxLayout(group_text)
        text_layout.setSpacing(10)
        
        # Tombol Add Text (Heading)
        btn_text = self._create_btn("T  Add Heading", "#2c313a", border=True)
        btn_text.clicked.connect(lambda: self.sig_add_text.emit("HEADING TEKS", 100))
        
        # Tombol Add Paragraph
        btn_para = self._create_btn("¶  Add Paragraph", "#2c313a", border=True)
        btn_para.clicked.connect(lambda: self.sig_add_text.emit("Lorem ipsum dolor sit amet, consectetur adipiscing elit.", 40))
        
        text_layout.addWidget(btn_text)
        text_layout.addWidget(btn_para)
        layout.addWidget(group_text)

        layout.addStretch()

    def _create_group(self, title):
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                color: #5c6370; 
                border: 1px solid #3e4451; 
                border-radius: 6px;
                margin-top: 12px; 
                padding-top: 10px;
            } 
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 5px; 
            }
        """)
        return group

    def _create_btn(self, text, bg_color, text_color="white", border=False):
        btn = QPushButton(text)
        border_style = "border: 1px solid #3e4451;" if border else "border: none;"
        btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {bg_color}; 
                color: {text_color}; 
                font-weight: bold; 
                padding: 12px; 
                border-radius: 4px;
                text-align: left;
                {border_style}
            }}
            QPushButton:hover {{ 
                background-color: {bg_color};
                filter: brightness(120%);
                border-color: #61afef;
            }}
        """)
        return btn

    def _on_add_media(self):
        data = MediaDialogService.get_media_file(self)
        if data:
            self.sig_request_import.emit(data['type'], data['path'])

    def _on_add_bg(self):
        data = MediaDialogService.get_media_file(self)
        if data:
            self.sig_set_background.emit(data['path'])