# gui/center_panel/canvas_items/grid_item.py
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import QRectF, Qt

class GridItem(QGraphicsItem):
    def __init__(self, w, h, gap=100):
        super().__init__()
        self.w = w
        self.h = h
        self.gap = gap
        
        # --- 4. Z-VALUE GRID ---
        self.setZValue(-500) 
        
        self.visible = False
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self):
        return QRectF(0, 0, self.w, self.h)

    def paint(self, painter, option, widget):
        if not self.visible: return

        pen = QPen(QColor(255, 255, 255, 40)) 
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        for x in range(0, int(self.w), self.gap):
            painter.drawLine(x, 0, x, int(self.h))

        for y in range(0, int(self.h), self.gap):
            painter.drawLine(0, y, int(self.w), y)

    def update_size(self, w, h):
        self.w = w
        self.h = h
        self.update()