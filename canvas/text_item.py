# canvas/text_item.py
from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtGui import QFont, QColor, QPen
from PySide6.QtCore import Qt

class TextItem(QGraphicsTextItem):
    def __init__(self, layer_id, text="New Text"):
        super().__init__(text)
        self.layer_id = layer_id
        
        # [BARU] Default Time
        self.start_time = 0.0
        self.duration = 5.0
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self._font_family = "Arial"
        self._font_size = 60
        self._color = "#ffffff"
        self._is_bold = False
        self._apply_style()
        self.setZValue(0)

    # ... (Method _apply_style & paint TETAP SAMA) ...
    def _apply_style(self):
        font = QFont(self._font_family, self._font_size)
        font.setBold(self._is_bold)
        self.setFont(font)
        self.setDefaultTextColor(QColor(self._color))

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.setPen(QPen(QColor("#ff00cc"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def update_properties(self, props: dict, z_index: int = 0):
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "rotation" in props: self.setRotation(props["rotation"])
        if "text_content" in props: self.setPlainText(props["text_content"])
        
        # [BARU] Update Time Properties
        if "start_time" in props: self.start_time = float(props["start_time"])
        if "duration" in props: self.duration = float(props["duration"])

        # Style Update
        style_changed = False
        if "font_family" in props: 
            self._font_family = props["font_family"]
            style_changed = True
        if "font_size" in props: 
            self._font_size = int(props["font_size"])
            style_changed = True
        if "text_color" in props: 
            self._color = props["text_color"]
            style_changed = True
        if "is_bold" in props: 
            self._is_bold = bool(props["is_bold"])
            style_changed = True
            
        if style_changed:
            self._apply_style()

        self.setZValue(z_index)

    # [BARU] Logic Timeline
    def update_time(self, current_time):
        end_time = self.start_time + self.duration
        
        if self.start_time <= current_time < end_time:
            if not self.isVisible():
                self.setVisible(True)
        else:
            if self.isVisible():
                self.setVisible(False)