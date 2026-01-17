from PySide6.QtWidgets import QGraphicsItem, QWidget
from PySide6.QtGui import QImage, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRectF

from engine.video_service import PREVIEW_SERVICE
from engine.chroma_processor import ChromaProcessor

class VideoItem(QGraphicsItem):
    """
    Custom Graphics Item yang merender QImage secara langsung.
    Mendukung transparansi (Alpha Channel) penuh untuk Chroma Key.
    """
    def __init__(self, layer_id, path=None):
        super().__init__()
        self.layer_id = layer_id
        self.path = path
        
        self.start_offset = 0.0 
        self.duration = 5.0
        
        # Properti Visual
        self.width = 1920
        self.height = 1080
        self.opacity = 1.0
        
        # Chroma State
        self.chroma_active = False
        self.chroma_color = "#00ff00"
        self.chroma_threshold = 0.15
        
        # Buffer Gambar (Disimpan agar paint event tidak perlu decode ulang)
        self._current_image = None
        
        # Flags Standar Editor
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable | 
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        # Inisialisasi Dummy
        self._generate_dummy()

    def _generate_dummy(self):
        self._current_image = QImage(320, 180, QImage.Format_ARGB32)
        self._current_image.fill(QColor("#333333"))
        self.width = 320
        self.height = 180
        self.update() # Request Redraw

    def boundingRect(self):
        # Mendefinisikan area klik dan refresh item
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter: QPainter, option, widget: QWidget = None):
        """
        Fungsi penggambaran kustom.
        Dipanggil otomatis oleh QGraphicsView setiap kali update() dipanggil.
        """
        # 1. Gambar Gambar Utama
        if self._current_image and not self._current_image.isNull():
            # Set Opacity Layer
            painter.setOpacity(self.opacity)
            
            # Gambar QImage pada koordinat (0,0) item
            # QImage yang sudah diproses ChromaProcessor memiliki Alpha channel
            # QPainter akan otomatis memblendingnya dengan background scene
            painter.drawImage(0, 0, self._current_image)

        # 2. Gambar Garis Seleksi (UI Helper)
        if self.isSelected():
            painter.setOpacity(1.0) # Reset opacity untuk garis
            painter.setPen(QPen(QColor("#00aaff"), 3, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def update_properties(self, props: dict, z_index: int = None):
        # Update Transform (Memakai API QGraphicsItem)
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "rotation" in props: self.setRotation(props["rotation"])
        if "opacity" in props: self.opacity = props["opacity"]
        
        if "start_time" in props: 
            self.start_offset = float(props["start_time"])
        
        # Update Chroma Settings
        if "chroma_active" in props: self.chroma_active = props["chroma_active"]
        if "chroma_color" in props: self.chroma_color = props["chroma_color"]
        if "chroma_threshold" in props: self.chroma_threshold = float(props["chroma_threshold"])
        
        if z_index is not None:
            self.setZValue(z_index)
            
        self.update() # Memicu paint()

    def sync_frame(self, global_time: float):
        """
        Dipanggil oleh PreviewPanel saat scrubbing/play.
        """
        local_time = global_time - self.start_offset
        if local_time < 0: local_time = 0
        
        # A. Ambil Image Raw
        qimg = PREVIEW_SERVICE.get_frame_image(self.path, local_time)
        
        if qimg.isNull(): return

        # B. Terapkan Chroma Key (Proses di CPU sebelum Paint)
        if self.chroma_active:
            qimg = ChromaProcessor.process_qimage(
                qimg, 
                self.chroma_color, 
                self.chroma_threshold
            )
            
        # C. Simpan ke Buffer & Trigger Repaint
        self._current_image = qimg
        
        # Jika ukuran video berubah (jarang, tapi mungkin), update bounding rect
        if self.width != qimg.width() or self.height != qimg.height():
            self.prepareGeometryChange() # Memberitahu scene ukuran berubah
            self.width = qimg.width()
            self.height = qimg.height()
        
        self.update() # Memicu pemanggilan method paint() di atas
        
    # Helper kompatibilitas
    def update_time(self, current_time):
        end_time = self.start_offset + self.duration
        self.setVisible(self.start_offset <= current_time < end_time)