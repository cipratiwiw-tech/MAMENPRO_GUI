# gui/center_panel/canvas_items/canvas_frame.py
from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtGui import QPen, QColor, QBrush

class CanvasFrameItem(QGraphicsRectItem):
    def __init__(self, width=1920, height=1080):
        super().__init__(0, 0, width, height)
        
        self.setPen(QPen(QColor("#FFFFFF"), 2)) 
        self.setBrush(QBrush(QColor("#000000"))) 
        
        # --- 4. Z-VALUE CANVAS FRAME ---
        self.setZValue(-1000)
        
        self.grid_item = None

    def update_size(self, w, h):
        self.setRect(0, 0, w, h)
        if self.grid_item:
            self.grid_item.update_size(w, h)

    def set_grid(self, grid_item):
        self.grid_item = grid_item
        self.grid_item.setParentItem(self)