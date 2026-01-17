from PySide6.QtGui import QImage, QPainter, QColor, QFont, QPen
from PySide6.QtCore import Qt, QRectF

from manager.timeline.layer_model import LayerModel
from engine.video_service import VideoService
from engine.chroma_processor import ChromaProcessor # <--- IMPORT BARU

class Compositor:
    def __init__(self, video_provider, width=1920, height=1080):
        self.width = width
        self.height = height
        self.vs = video_provider # <--- Dependency Injection (VideoService Private)

    def compose_frame(self, t: float, active_layers: list) -> QImage:
        # Canvas Kosong
        canvas = QImage(self.width, self.height, QImage.Format_ARGB32_Premultiplied)
        canvas.fill(QColor("#000000"))

        # 2. Siapkan Painter
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # 3. Loop Layer dari Bawah ke Atas (Sesuai Z-Index yang sudah disort TimelineEngine)
        for layer in active_layers:
            self._draw_layer(painter, layer, t)

        painter.end()
        return canvas

    def _draw_layer(self, painter: QPainter, layer: LayerModel, global_time: float):
        """Logika menggambar per tipe layer"""
        props = layer.payload # Data properti visual (x, y, scale, dll)
        
        # Ambil properti transform standar
        x = props.get("x", 0)
        y = props.get("y", 0)
        scale = props.get("scale", 100) / 100.0
        opacity = props.get("opacity", 1.0)
        rotation = props.get("rotation", 0)

        # Simpan state painter sebelum transformasi
        painter.save()
        
        # --- A. VIDEO LAYER ---
        if layer.type == "video":
            path = props.get("path")
            start_offset = props.get("start_time", 0.0) # Offset waktu
            
            # Hitung waktu lokal
            local_time = global_time - start_offset
            if local_time < 0: local_time = 0
            
            # PAKE PROVIDER KHUSUS (Bukan Global)
            # Dan minta QImage langsung (get_frame_image), bukan QPixmap
            qimg = self.vs.get_frame_image(path, local_time)
            
            if not qimg.isNull():
                # 2. CEK EFEK CHROMA KEY
                if props.get("chroma_active", False):
                    c_color = props.get("chroma_color", "#00ff00")
                    c_thresh = float(props.get("chroma_threshold", 0.3))
                    
                    # PROSES! (Hijau jadi Transparan)
                    qimg = ChromaProcessor.process_qimage(qimg, c_color, c_thresh)

                # 3. Transform & Gambar (Sama seperti sebelumnya)
                painter.translate(props.get("x", 0), props.get("y", 0))
                painter.rotate(props.get("rotation", 0))
                scale = props.get("scale", 100) / 100.0
                painter.scale(scale, scale)
                painter.setOpacity(props.get("opacity", 1.0))
                
                painter.drawImage(0, 0, qimg)

        # --- B. TEXT LAYER ---
        elif layer.type == "text":
            text_content = props.get("text_content", "Text")
            font_family = props.get("font_family", "Arial")
            font_size = int(props.get("font_size", 60))
            color = props.get("text_color", "#ffffff")
            
            # Apply Transform
            painter.translate(x, y)
            painter.rotate(rotation)
            painter.scale(scale, scale)
            painter.setOpacity(opacity)
            
            # Setup Font
            font = QFont(font_family, font_size)
            if props.get("is_bold"): font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(QColor(color)))
            
            # Draw Text
            # (Sederhana dulu, belum ada wrap text kompleks)
            painter.drawText(0, font_size, text_content) 

        painter.restore()