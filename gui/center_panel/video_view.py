from PySide6.QtWidgets import QGraphicsView, QFrame, QGraphicsRectItem, QGraphicsPathItem
from PySide6.QtGui import QPainter, QMouseEvent, QWheelEvent, QBrush, QColor, QPen, QPainterPath, QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtCore import Qt, Signal

# Import hanya untuk pengecekan tipe (agar View tau mana yang VideoItem)
from gui.center_panel.video_item import VideoItem 

class CanvasContainer(QGraphicsRectItem):
    def __init__(self, w, h):
        super().__init__(0, 0, w, h)
        self.setBrush(QBrush(QColor("#1e1e1e")))
        self.setPen(QPen(QColor("#333333"), 1))
        self.setZValue(0)

class DimmingOverlay(QGraphicsPathItem):
    def __init__(self, canvas_rect):
        super().__init__()
        self.setBrush(QBrush(QColor(0, 0, 0, 180)))
        self.setPen(Qt.NoPen)
        self.setZValue(10)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.update_mask(canvas_rect)

    def update_mask(self, canvas_rect):
        path = QPainterPath()
        path.addRect(-50000, -50000, 100000, 100000) # Area infinite gelap
        path.addRect(canvas_rect) # Area terang (lubang)
        self.setPath(path)

class VideoGraphicsView(QGraphicsView):
    # [BARU] Sinyal saat ada file di-drop
    sig_dropped = Signal()
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setAlignment(Qt.AlignCenter)
        self.setBackgroundBrush(QBrush(QColor("#0a0a0a")))
        self.setFrameShape(QFrame.NoFrame)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate) 
        # [BARU] Aktifkan Drop dari Eksternal
        self.setAcceptDrops(True)
        self._last_target_item = None

    def wheelEvent(self, event: QWheelEvent):
        # Zoom Logic
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event: QMouseEvent):
        # Pan Logic (Spasi/Ctrl + Click)
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            # Fake event agar View langsung merespon drag
            fake = QMouseEvent(event.type(), event.position(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
            super().mousePressEvent(fake)
            return

        # Selection Logic
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.position().toPoint())
            item = self.scene().itemAt(pos, self.transform())
            
            # Jika klik VideoItem -> Mode Select biasa
            if isinstance(item, VideoItem): 
                self.setDragMode(QGraphicsView.NoDrag)
            # Jika klik background -> Mode RubberBand (kotak seleksi biru)
            else:
                self.setDragMode(QGraphicsView.RubberBandDrag)
                
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        self.setDragMode(QGraphicsView.NoDrag)
        
    # [BARU] 1. Saat File Masuk ke Area Canvas
    def dragEnterEvent(self, event: QDragEnterEvent):
        # Cek apakah yang dibawa adalah file/URL
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    # [BARU] 2. Saat File Digeser-geser (Hit Testing Real-time)
    def dragMoveEvent(self, event: QDragMoveEvent):
        # Logic Hit Testing: Posisi mouse di layar -> Posisi Scene
        pos = self.mapToScene(event.position().toPoint())
        
        # Ambil semua item di bawah kursor
        items = self.scene().items(pos)
        
        # Cari VideoItem teratas (yang bukan background/guide)
        target = None
        for item in items:
            if isinstance(item, VideoItem):
                # Opsional: Jika tidak ingin drop ke background, tambahkan cek: 
                # if not isinstance(item, BackgroundItem):
                target = item
                break
        
        # Update Visual Feedback
        if target != self._last_target_item:
            # Matikan highlight item lama
            if self._last_target_item:
                self._last_target_item.set_drop_highlight(False)
            
            # Nyalakan highlight item baru
            if target:
                target.set_drop_highlight(True)
            
            self._last_target_item = target

        if target:
            event.accept()
        else:
            event.ignore()

    # [BARU] 3. Saat File Dilepas (Drop)
    def dropEvent(self, event: QDropEvent):
        # Bersihkan highlight terakhir
        if self._last_target_item:
            self._last_target_item.set_drop_highlight(False)
            self._last_target_item = None

        # Ambil path file
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if not urls: return
            
            # Ambil file pertama saja
            file_path = urls[0].toLocalFile()
            
            # Hit Testing sekali lagi untuk memastikan target
            pos = self.mapToScene(event.position().toPoint())
            items = self.scene().items(pos)
            
            for item in items:
                if isinstance(item, VideoItem):
                    # [INTI LOGIKA] Masukkan path ke property item dan render visualnya
                    print(f"[DROP] File: {file_path} -> Layer: {item.name}")
                    
                    # Method set_content di VideoItem akan otomatis:
                    # 1. Menyimpan path ke self.file_path (preview_source)
                    # 2. Merender pixmap baru
                    # 3. Memanggil update()
                    item.set_content(file_path) 
                    
                    # Update settings agar controller (LayerPanel) tersinkronisasi
                    # (Opsional: controller biasanya listen sinyal selection/change)
                    item.settings["content_type"] = "media"
                    # [PENTING] Emit sinyal ke Controller
                    self.sig_dropped.emit()
                    event.accept()
                    return

    # [BARU] 4. Saat Drag Keluar dari Aplikasi (Cleanup)
    def dragLeaveEvent(self, event):
        if self._last_target_item:
            self._last_target_item.set_drop_highlight(False)
            self._last_target_item = None
        super().dragLeaveEvent(event)