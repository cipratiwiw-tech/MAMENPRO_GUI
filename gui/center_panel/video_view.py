# gui/center_panel/video_view.py
from PySide6.QtWidgets import QGraphicsView, QFrame, QGraphicsRectItem, QGraphicsPathItem
from PySide6.QtGui import QPainter, QMouseEvent, QWheelEvent, QBrush, QColor, QPen, QPainterPath, QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtCore import Qt, Signal

# Import hanya untuk pengecekan tipe
from canvas.video_item import VideoItem 

class CanvasContainer(QGraphicsRectItem):
    def __init__(self, w, h):
        super().__init__(0, 0, w, h)
        self.setBrush(QBrush(QColor("#1e1e1e")))
        self.setPen(QPen(QColor("#333333"), 1))
        self.setZValue(-2000) # Paling belakang

class DimmingOverlay(QGraphicsPathItem):
    def __init__(self, canvas_rect):
        super().__init__()
        self.setBrush(QBrush(QColor(0, 0, 0, 180)))
        self.setPen(Qt.NoPen)
        self.setZValue(10000) # Paling depan (Overlay)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.update_mask(canvas_rect)

    def update_mask(self, canvas_rect):
        path = QPainterPath()
        path.addRect(-50000, -50000, 100000, 100000) # Area infinite gelap
        path.addRect(canvas_rect) # Lubang (Area terang)
        self.setPath(path)

class VideoGraphicsView(QGraphicsView):
    sig_dropped = Signal()

    def __init__(self, scene):
        super().__init__(scene)
        
        # 1. VISUAL SETUP
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setBackgroundBrush(QBrush(QColor("#151515")))
        self.setFrameShape(QFrame.NoFrame)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate) 
        
        # 2. HILANGKAN SCROLLBARS (Sesuai Request)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 3. INTERAKSI ZOOM
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        # 4. DRAG & DROP
        self.setAcceptDrops(True)
        self._last_target_item = None
        
        # 5. PANNING STATE
        self._is_panning = False
        self._pan_start = None

    # --- ZOOM LOGIC (Scroll Mouse) ---
    def wheelEvent(self, event: QWheelEvent):
        # Paksa event diterima agar tidak menggeser scrollbar (walaupun hidden)
        event.accept()

        # Logika Zoom Smooth
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        # Arah Scroll
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    # --- PANNING LOGIC (Middle Click / Alt+Click) ---
    def mousePressEvent(self, event: QMouseEvent):
        # Middle click atau Alt+Click untuk geser canvas
        if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and event.modifiers() == Qt.AltModifier):
            self._is_panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return # Jangan teruskan ke super() agar tidak select item

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            
            # Geser scrollbar manual
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
            
        super().mouseReleaseEvent(event)

    # --- DRAG & DROP LOGIC (Tetap pertahankan yang lama jika mau) ---
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    # (Sisa method dragMoveEvent, dropEvent, dragLeaveEvent bisa dibiarkan sama seperti file asli Anda jika logikanya sudah benar untuk kebutuhan Drop File)
    # ... (Salin bagian Drop Event dari file lama Anda jika perlu, atau gunakan versi preview_panel sebelumnya yang lebih sederhana untuk video item)

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