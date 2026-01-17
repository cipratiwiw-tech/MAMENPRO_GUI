# gui/center_panel/canvas_items/canvas_frame.py
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsLineItem
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtCore import Qt

class CanvasFrameItem(QGraphicsRectItem):
    """
    Frame utama yang menjadi parent semua layer.
    Memiliki fitur Smart Guides (Garis magnet).
    """
    def __init__(self, width=1920, height=1080):
        super().__init__(0, 0, width, height)
        
        # Visual Border Frame
        self.setPen(QPen(QColor("#FFFFFF"), 2)) 
        self.setBrush(QBrush(QColor("#000000"))) # Background Hitam
        self.setZValue(-1000) # Paling belakang
        
        self.grid_item = None
        
        # --- SMART GUIDES (GARIS MAGNET) ---
        # Kita gunakan garis solid tipis berwarna Cyan terang agar kontras
        pen_guide = QPen(QColor("#00FFFF"), 1) # Cyan
        # pen_guide.setStyle(Qt.DashLine) # Opsional: Putus-putus
        
        # Garis Vertikal (Tengah X)
        self.guide_v = QGraphicsLineItem(self)
        self.guide_v.setPen(pen_guide)
        self.guide_v.setZValue(99999) # Selalu paling atas
        self.guide_v.hide()
        
        # Garis Horizontal (Tengah Y)
        self.guide_h = QGraphicsLineItem(self)
        self.guide_h.setPen(pen_guide)
        self.guide_h.setZValue(99999)
        self.guide_h.hide()

    def update_size(self, w, h):
        self.setRect(0, 0, w, h)
        
        # Update posisi garis guide pas di tengah
        cx, cy = w / 2, h / 2
        
        # Garis membelah dari ujung ke ujung
        self.guide_v.setLine(cx, 0, cx, h)
        self.guide_h.setLine(0, cy, w, cy)
        
        if self.grid_item:
            self.grid_item.update_size(w, h)

    def set_grid(self, grid_item):
        self.grid_item = grid_item
        self.grid_item.setParentItem(self)

    # --- API CONTROL GUIDES ---
    
    def show_guide_vertical(self, visible):
        if self.guide_v.isVisible() != visible:
            self.guide_v.setVisible(visible)

    def show_guide_horizontal(self, visible):
        if self.guide_h.isVisible() != visible:
            self.guide_h.setVisible(visible)