from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtGui import QFont, QColor, QPen
from PySide6.QtCore import Qt

class TextItem(QGraphicsTextItem):
    def __init__(self, layer_id, text="New Text"):
        super().__init__(text)
        self.layer_id = layer_id
        
        # ❌ HAPUS: self.start_time & self.duration
        # Item ini sekarang 'abadi' di mata internalnya.
        # Visibility diatur eksternal oleh PreviewPanel.
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        # Default Style
        self._font_family = "Arial"
        self._font_size = 60
        self._color = "#ffffff"
        self._is_bold = False
        
        self._apply_style()
        self.setZValue(0)

    def _apply_style(self):
        font = QFont(self._font_family, self._font_size)
        font.setBold(self._is_bold)
        self.setFont(font)
        self.setDefaultTextColor(QColor(self._color))

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            # Visual feedback saat dipilih (garis putus-putus)
            painter.setPen(QPen(QColor("#ff00cc"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def update_properties(self, props: dict, z_index: int = None):
        # 1. Transform & Content
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "rotation" in props: self.setRotation(props["rotation"])
        if "text_content" in props: self.setPlainText(props["text_content"])
        
        # ❌ HAPUS: if "start_time" ...
        # ❌ HAPUS: if "duration" ...

        # 2. Styling
        style_changed = False
        if "font_family" in props: 
            self._font_family = props["font_family"]; style_changed = True
        if "font_size" in props: 
            self._font_size = int(props["font_size"]); style_changed = True
        if "text_color" in props: 
            self._color = props["text_color"]; style_changed = True
        if "is_bold" in props: 
            self._is_bold = bool(props["is_bold"]); style_changed = True
            
        if style_changed:
            self._apply_style()

        # 3. Z-Index
        if z_index is not None:
            self.setZValue(z_index)

    def sync_frame(self, t: float):
        # Placeholder untuk fitur masa depan (misal: Text Karaoke / Typewriter effect)
        # Saat ini biarkan kosong.
        pass