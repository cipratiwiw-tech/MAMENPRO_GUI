from PySide6.QtWidgets import QGraphicsRectItem
# [UBAH DI SINI] Tambahkan QRect (tanpa F)
from PySide6.QtCore import Qt, QRectF, QRect 
from PySide6.QtGui import QFont, QFontMetrics, QColor, QPen, QBrush

from gui.center_panel.video_item import VideoItem

class CaptionItem(VideoItem):
    def __init__(self, name="CAPTION_LAYER", *args, **kwargs):
        # Panggil init milik VideoItem agar semua fitur dasar (drag, select) tetap jalan
        super().__init__(name, *args, **kwargs)
        
        # Setting khusus default untuk caption
        self.settings.update({
            "content_type": "caption_preview",
            "frame_w": 0, # Nanti dihitung otomatis
            "frame_h": 0,
            # Matikan fitur resize manual di settings jika ada flag-nya
            "lock_aspect_ratio": True 
        })
        
        # Caption biasanya tidak punya durasi potong di preview dummy
        self.set_time_range(0, None)

    def auto_fit_content(self):
        s = self.settings
        
        font = QFont(s.get("font", "Arial"), s.get("font_size", 40))
        weight = s.get("font_weight", "Normal")
        if weight == "Bold": font.setBold(True)
        elif weight == "Black": font.setWeight(QFont.Black)
        elif weight == "Light": font.setWeight(QFont.Light)
        
        text = s.get("text_content", "SAMPLE")
        
        fm = QFontMetrics(font)
        
        # [PERBAIKAN ERROR DI SINI]
        # Gunakan QRect() bukan QRectF() karena QFontMetrics butuh integer
        text_rect = fm.boundingRect(QRect(0, 0, 0, 0), Qt.AlignCenter, text)
        
        padding = 30 
        new_w = text_rect.width() + padding
        new_h = text_rect.height() + padding
        
        self.setRect(0, 0, new_w, new_h)
        self.settings["frame_w"] = new_w
        self.settings["frame_h"] = new_h
        
        self.setTransformOriginPoint(new_w / 2, new_h / 2)

    # Override fungsi refresh_text_render dari parent
    def refresh_text_render(self):
        # 1. Hitung ukuran dulu sebelum render
        self.auto_fit_content()
        
        # 2. Panggil logika render parent (VideoItem) untuk menggambar teks & background
        # Karena kita sudah mengubah self.rect() di atas, parent akan menggambar sesuai ukuran baru.
        super().refresh_text_render()

    # Override paint_ui_helpers agar TIDAK muncul kotak resize di pojok
    def _paint_ui_helpers(self, painter):
        # Kita gambar garis putus-putus simpel saja tanpa handle resize
        # karena caption ukurannya otomatis, user tidak boleh tarik-tarik ujungnya.
        r = self.rect()
        
        # Garis batas seleksi
        pen = QPen(QColor("#00ff00"), 2, Qt.DashLine) # Warna Hijau terang
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(r)
        
        # Label kecil di atas (Optional)
        if self.isSelected():
            painter.setBrush(QColor("#00ff00"))
            painter.drawRect(0, -20, r.width(), 20)
            painter.setPen(Qt.black)
            font = QFont("Arial", 8, QFont.Bold)
            painter.setFont(font)
            painter.drawText(QRectF(0, -20, r.width(), 20), Qt.AlignCenter, "CAPTION (AUTO-SIZE)")