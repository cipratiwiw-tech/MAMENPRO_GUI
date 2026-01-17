# engine/render_engine.py
import cv2
import numpy as np
from PIL import Image
from PySide6.QtGui import QImage, QPainter, QColor

# ✅ HAPUS import Compositor yang tidak perlu
from engine.ffmpeg_renderer import FFmpegRenderer

class RenderEngine:
    def __init__(self, timeline, video_service):
        self.timeline = timeline
        self.video_service = video_service
        
        # ❌ HAPUS BARIS INI (Penyebab Error):
        # self.compositor = Compositor() 
        
        self.renderer = FFmpegRenderer()

    def render(self, output_path, settings, callback=None):
        fps = settings.get("fps", 30)
        quality = settings.get("quality", "Medium (CRF 23)")
        
        crf_map = {
            "High (CRF 18)": 18,
            "Medium (CRF 23)": 23,
            "Low (CRF 28)": 28
        }
        crf = crf_map.get(quality, 23)

        duration = self.timeline.get_total_duration()
        total_frames = int(duration * fps)
        
        # Default Resolution (Bisa diambil dari settings jika ada)
        width, height = 1920, 1080 
        
        self.renderer.start(output_path, width, height, fps, crf)

        try:
            for frame_idx in range(total_frames):
                current_time = frame_idx / float(fps)
                
                # 1. Ambil Layer Aktif
                active_layers = self.timeline.get_active_layers(current_time)
                
                # 2. Siapkan Canvas
                canvas = QImage(width, height, QImage.Format_ARGB32)
                canvas.fill(QColor(0, 0, 0, 0)) # Transparan/Hitam
                
                painter = QPainter(canvas)
                
                # 3. Urutkan Layer (Z-Index terendah di bawah)
                active_layers.sort(key=lambda x: x.z_index)
                
                for layer in active_layers:
                    # Ambil Frame dari VideoService
                    layer_path = layer.payload.get("path")
                    if layer_path:
                        local_time = current_time - layer.time.start
                        img = self.video_service.get_frame_image(layer_path, local_time)
                        
                        if img and not img.isNull():
                            # Ambil Properti Transform
                            props = layer.payload
                            x = props.get("x", 0)
                            y = props.get("y", 0)
                            scale = props.get("scale", 100) / 100.0
                            rotation = props.get("rotation", 0)
                            opacity = props.get("opacity", 1.0)
                            
                            painter.save()
                            # Transformasi Geometri
                            painter.translate(x + img.width()/2, y + img.height()/2)
                            painter.rotate(rotation)
                            painter.scale(scale, scale)
                            painter.setOpacity(opacity)
                            # Gambar di tengah titik pivot
                            painter.drawImage(-img.width()/2, -img.height()/2, img)
                            painter.restore()
                            
                    elif layer.type == "text":
                        # (Opsional) Implementasi render teks di sini jika diperlukan
                        pass
                
                painter.end()
                
                # 4. Tulis ke Video
                self.renderer.write_frame(canvas)
                
                # 5. Update Progress
                if callback:
                    percent = int((frame_idx / total_frames) * 100)
                    callback(percent)
                    
        finally:
            self.renderer.stop()