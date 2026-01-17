# gui/center_panel/canvas_items/canvas_frame.py
from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtGui import QPen, QColor, QBrush

class CanvasFrameItem(QGraphicsRectItem):
    """
    Frame utama yang menjadi parent semua layer.
    """
    def __init__(self, width=1920, height=1080):
        super().__init__(0, 0, width, height)
        
        # Visual Border Putih Tipis
        self.setPen(QPen(QColor("#FFFFFF"), 2)) 
        self.setBrush(QBrush(QColor("#000000"))) # Background Hitam
        
        # Z-Value paling belakang
        self.setZValue(-1000)
        
        self.grid_item = None

    def update_size(self, w, h):
        # Update ukuran kotak hitam
        self.setRect(0, 0, w, h)
        
        # 🔥 UPDATE JUGA UKURAN GRID (PENTING) 🔥
        if self.grid_item:
            self.grid_item.update_size(w, h)

    def set_grid(self, grid_item):
        self.grid_item = grid_item
        # Grid dijadikan child agar ikut bergerak jika frame digeser
        self.grid_item.setParentItem(self)