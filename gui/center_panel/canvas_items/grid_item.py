# gui/center_panel/canvas_items/grid_item.py
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import QRectF, Qt

class GridItem(QGraphicsItem):
    def __init__(self, w, h):
        super().__init__()
        self.w = w
        self.h = h
        self.visible = False
        
        # Grid ini transparan terhadap klik mouse (agar bisa klik video di bawahnya)
        self.setAcceptedMouseButtons(Qt.NoButton)
        # Z-Value tinggi agar selalu di atas video layer
        self.setZValue(9999) 

    def boundingRect(self):
        return QRectF(0, 0, self.w, self.h)

    def paint(self, painter, option, widget):
        if not self.visible: return

        # 1. Garis Tengah (Center Lines) - Warna Cyan Tegas
        # Membantu menaruh objek tepat di tengah canvas
        pen_center = QPen(QColor("#00FFFF"))
        pen_center.setWidth(1)
        pen_center.setStyle(Qt.SolidLine)
        painter.setPen(pen_center)
        
        cx, cy = self.w / 2, self.h / 2
        painter.drawLine(cx, 0, cx, self.h) # Garis Vertikal Tengah
        painter.drawLine(0, cy, self.w, cy) # Garis Horizontal Tengah

        # 2. Rule of Thirds (Garis Komposisi 1/3) - Putih Putus-putus
        # Membantu komposisi sinematik
        pen_thirds = QPen(QColor(255, 255, 255, 180)) # Putih agak transparan
        pen_thirds.setStyle(Qt.DashLine)
        painter.setPen(pen_thirds)

        # Vertikal 1/3 dan 2/3
        painter.drawLine(self.w/3, 0, self.w/3, self.h)
        painter.drawLine(self.w*2/3, 0, self.w*2/3, self.h)
        
        # Horizontal 1/3 dan 2/3
        painter.drawLine(0, self.h/3, self.w, self.h/3)
        painter.drawLine(0, self.h*2/3, self.w, self.h*2/3)

        # 3. Safe Margins (Action Safe 10%) - Abu Tipis
        # Membantu agar teks tidak terpotong di layar HP/TV lengkung
        pen_safe = QPen(QColor(255, 255, 255, 50))
        pen_safe.setStyle(Qt.DotLine)
        painter.setPen(pen_safe)
        
        margin_x = self.w * 0.1
        margin_y = self.h * 0.1
        painter.drawRect(margin_x, margin_y, self.w - 2*margin_x, self.h - 2*margin_y)

    def update_size(self, w, h):
        """Update ukuran grid saat rasio canvas berubah"""
        self.prepareGeometryChange()
        self.w = w
        self.h = h
        self.update() # Trigger repaint