# canvas/text_item.py
from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtGui import QFont, QColor, QPen
from PySide6.QtCore import Qt

class TextItem(QGraphicsTextItem):
    def __init__(self, layer_id, text="New Text"):
        super().__init__(text)
        self.layer_id = layer_id
        
        # Flags interaksi dasar
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        # Default State Visual
        self._font_family = "Arial"
        self._font_size = 60
        self._color = "#ffffff"
        self._is_bold = False
        
        self._apply_style()

    def _apply_style(self):
        # Setup Font
        font = QFont(self._font_family, self._font_size)
        font.setBold(self._is_bold)
        self.setFont(font)
        
        # Setup Color
        self.setDefaultTextColor(QColor(self._color))

    def paint(self, painter, option, widget=None):
        # Render teks asli
        super().paint(painter, option, widget)
        
        # Render border seleksi putus-putus
        if self.isSelected():
            painter.setPen(QPen(QColor("#ff00cc"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def update_properties(self, props: dict):
        """Menerima update parsial dari Logic"""
        needs_style_update = False

        # 1. Transform Basics
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "rotation" in props: self.setRotation(props["rotation"])
        if "opacity" in props: self.setOpacity(props["opacity"])

        # 2. Text Content
        if "text_content" in props: 
            self.setPlainText(props["text_content"])

        # 3. Styling Logic
        if "font_family" in props:
            self._font_family = props["font_family"]
            needs_style_update = True
            
        if "font_size" in props:
            self._font_size = int(props["font_size"])
            needs_style_update = True
            
        if "text_color" in props:
            self._color = props["text_color"]
            needs_style_update = True
            
        if "is_bold" in props:
            self._is_bold = bool(props["is_bold"])
            needs_style_update = True

        if needs_style_update:
            self._apply_style()