# canvas/text_item.py
from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtGui import QFont, QColor, QPen
from PySide6.QtCore import Qt

class TextItem(QGraphicsTextItem):
    """
    Representasi visual untuk Text di Canvas.
    """
    def __init__(self, layer_id, text="New Text"):
        super().__init__(text)
        self.layer_id = layer_id
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        # Default Style
        self.setDefaultTextColor(QColor("white"))
        self.setFont(QFont("Arial", 40, QFont.Bold))

    def paint(self, painter, option, widget=None):
        # Render text
        super().paint(painter, option, widget)
        
        # Render border seleksi
        if self.isSelected():
            painter.setPen(QPen(QColor("#ff00cc"), 2, Qt.DotLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def update_properties(self, props: dict):
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "rotation" in props: self.setRotation(props["rotation"])
        if "text_content" in props: self.setPlainText(props["text_content"])
        # Bisa tambah font, color, dll sesuai kebutuhan