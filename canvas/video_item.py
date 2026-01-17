# canvas/video_item.py
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtGui import QPixmap, QColor, QPen
from PySide6.QtCore import Qt

# 1. Import Service & Processor
from engine.video_service import PREVIEW_SERVICE
from engine.chroma_processor import ChromaProcessor

class VideoItem(QGraphicsPixmapItem):
    def __init__(self, layer_id, path=None):
        super().__init__()
        self.layer_id = layer_id
        self.path = path
        
        self.start_offset = 0.0 
        
        # Simpan State Chroma Lokal
        self.chroma_active = False
        self.chroma_color = "#00ff00"
        self.chroma_threshold = 0.15
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable | 
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self._load_dummy_content()
        
    def _load_dummy_content(self):
        pix = QPixmap(320, 180)
        pix.fill(QColor("#333333"))
        self.setPixmap(pix)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.setPen(QPen(QColor("#00aaff"), 3, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def update_properties(self, props: dict, z_index: int = None):
        # 1. Transform
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "rotation" in props: self.setRotation(props["rotation"])
        if "opacity" in props: self.setOpacity(props["opacity"])
        
        if "start_time" in props: 
            self.start_offset = float(props["start_time"])
        
        # 2. CHROMA UPDATE (Simpan setting ke variabel lokal)
        if "chroma_active" in props: 
            self.chroma_active = props["chroma_active"]
        if "chroma_color" in props: 
            self.chroma_color = props["chroma_color"]
        if "chroma_threshold" in props: 
            self.chroma_threshold = float(props["chroma_threshold"])
        
        # 3. Z-Index
        if z_index is not None:
            self.setZValue(z_index)
            
        # [PENTING] Force refresh visual saat properti berubah (agar efek langsung terlihat)
        # Kita panggil sync_frame dengan waktu "dummy" atau current time dari engine kalau bisa
        # Di sini kita biarkan preview engine yang memanggil sync_frame via timer

    def sync_frame(self, global_time: float):
        """
        Render Frame + Efek Realtime
        """
        local_time = global_time - self.start_offset
        if local_time < 0: local_time = 0
        
        # A. Minta QImage (Data Mentah) bukan QPixmap
        # Kita butuh pixel data untuk diproses OpenCV
        qimg = PREVIEW_SERVICE.get_frame_image(self.path, local_time)
        
        if qimg.isNull(): return

        # B. Terapkan Chroma Key Jika Aktif
        if self.chroma_active:
            qimg = ChromaProcessor.process_qimage(
                qimg, 
                self.chroma_color, 
                self.chroma_threshold
            )
        
        # C. Konversi ke QPixmap untuk Tampil di Layar
        self.setPixmap(QPixmap.fromImage(qimg))