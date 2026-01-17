# gui/left_panel/graphics_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import Signal, Qt

class GraphicsPanel(QWidget):
    # Signal: path
    sig_add_graphic = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl = QLabel("GRAPHICS & OVERLAYS")
        lbl.setStyleSheet("font-weight: bold; color: #c678dd; margin-bottom: 5px;")
        layout.addWidget(lbl)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("border: 1px solid #3e4451;")
        
        # Mock Data (Idealnya scan folder assets)
        graphics = [
            ("🔴 Rec Overlay", "assets/graphics/rec_overlay.png"),
            ("🔥 Fire Emoji", "assets/graphics/emoji_fire.png"),
            ("👍 Like Button", "assets/graphics/sticker_like.png"),
            ("⭐ Star Icon", "assets/graphics/star.png")
        ]
        
        for name, path in graphics:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, path)
            self.list_widget.addItem(item)
            
        self.list_widget.itemDoubleClicked.connect(self._on_dbl_click)
        layout.addWidget(self.list_widget)
        
        lbl_hint = QLabel("Simulasi: Double click untuk menambahkan")
        lbl_hint.setStyleSheet("color: #5c6370; font-size: 10px; font-style: italic;")
        layout.addWidget(lbl_hint)

    def _on_dbl_click(self, item):
        path = item.data(Qt.UserRole)
        self.sig_add_graphic.emit(path)
