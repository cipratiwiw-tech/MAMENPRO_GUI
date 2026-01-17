# engine/render_engine.py
import cv2
import numpy as np
import subprocess
import os
import tempfile
from PySide6.QtGui import QImage, QPainter, QColor, QFont, QPen, QFontMetrics
from PySide6.QtCore import Qt, QRectF

from engine.ffmpeg_renderer import FFmpegRenderer
from engine.chroma_processor import ChromaProcessor # Pastikan ini diimport

class RenderEngine:
    def __init__(self, timeline, video_service):
        self.timeline = timeline
        self.video_service = video_service
        self.renderer = None 

    def render(self, output_path, settings, callback=None):
        fps = settings.get("fps", 30)
        
        # [NEW] AMBIL RESOLUSI DARI SETTINGS
        # Default fallback ke 1080x1920 jika tidak ada
        width = settings.get("width", 1080)
        height = settings.get("height", 1920)
        
        duration = self.timeline.get_total_duration()
        total_frames = int(duration * fps)
                
        # 1. AUDIO PROCESSING (Sama seperti sebelumnya)
        print("🔊 Processing Audio Mix...")
        temp_audio_path = os.path.join(tempfile.gettempdir(), "mamen_mix_temp.aac")
        has_audio = self._mix_audio(temp_audio_path)

        # 2. INIT RENDERER
        self.renderer = FFmpegRenderer(output_path, width, height, fps)
        
        if has_audio:
            self.renderer.start_process(audio_path=temp_audio_path, audio_delay_ms=0)
        else:
            self.renderer.start_process() 

        try:
            for frame_idx in range(total_frames):
                current_time = frame_idx / float(fps)
                
                active_layers = self.timeline.get_active_layers(current_time)
                active_layers.sort(key=lambda x: x.z_index) 
                
                # Canvas size dinamis
                canvas = QImage(width, height, QImage.Format_ARGB32)
                canvas.fill(QColor(0, 0, 0, 255)) 
                painter = QPainter(canvas)
                
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                painter.setRenderHint(QPainter.TextAntialiasing)
                
                for layer in active_layers:
                    self._draw_layer(painter, layer, current_time)
                
                painter.end()
                
                # D. Write Frame
                rgb_image = canvas.convertToFormat(QImage.Format_RGB888)
                raw_bytes = rgb_image.constBits().tobytes()
                self.renderer.write_frame(raw_bytes)
                
                # E. Callback
                if callback:
                    percent = int((frame_idx / total_frames) * 100)
                    callback(percent)
                    
        except Exception as e:
            print(f"🔥 Render Error: {e}")
            import traceback
            traceback.print_exc()
            raise e
            
        finally:
            if self.renderer:
                self.renderer.close_process()
                self.renderer = None
            if has_audio and os.path.exists(temp_audio_path):
                try: os.remove(temp_audio_path)
                except: pass

    def _draw_layer(self, painter: QPainter, layer, global_time):
        """
        Fungsi inti untuk menggambar satu layer ke canvas render.
        Menangani Video, Image, dan Text.
        """
        props = layer.payload
        layer_type = layer.type
        
        # Transformasi Dasar (X, Y, Scale, Rotation, Opacity)
        x = props.get("x", 0)
        y = props.get("y", 0)
        scale = props.get("scale", 100) / 100.0
        rotation = props.get("rotation", 0)
        opacity = props.get("opacity", 1.0)
        
        painter.save()
        
        # --- 1. HANDLE VIDEO / IMAGE ---
        if layer_type in ['video', 'image']:
            path = props.get("path")
            if path:
                # Hitung waktu lokal video
                start_offset = float(props.get("start_time", 0.0))
                local_time = global_time - start_offset
                
                # Ambil Frame dari VideoService
                qimg = self.video_service.get_frame_image(path, local_time)
                
                if qimg and not qimg.isNull():
                    # [CHROMA KEY LOGIC]
                    if props.get("chroma_active", False):
                        c_color = props.get("chroma_color", "#00ff00")
                        c_thresh = float(props.get("chroma_threshold", 0.15))
                        # Proses Chroma (Hijau -> Transparan)
                        qimg = ChromaProcessor.process_qimage(qimg, c_color, c_thresh)
                    
                    # Apply Transform
                    # Pivot point di tengah gambar (Sama seperti Preview)
                    w, h = qimg.width(), qimg.height()
                    painter.translate(x + (w*scale)/2, y + (h*scale)/2) # Pindah ke tengah target
                    painter.rotate(rotation)
                    painter.scale(scale, scale)
                    painter.setOpacity(opacity)
                    
                    # Gambar (offset -w/2, -h/2 agar pivot di tengah)
                    painter.drawImage(-w/2, -h/2, qimg)

        # --- 2. HANDLE TEXT / CAPTION ---
        elif layer_type in ['text', 'caption']:
            text_content = props.get("text_content", "Sample Text")
            font_family = props.get("font_family", "Arial")
            font_size = int(props.get("font_size", 60))
            color_hex = props.get("text_color", "#ffffff")
            is_bold = props.get("is_bold", False)
            
            # Setup Font
            font = QFont(font_family, font_size)
            font.setBold(is_bold)
            painter.setFont(font)
            painter.setPen(QColor(color_hex))
            
            # Hitung Ukuran Teks untuk Pivot Center
            fm = QFontMetrics(font)
            rect = fm.boundingRect(text_content)
            text_w = rect.width()
            text_h = rect.height()
            
            # Apply Transform
            # Asumsi X,Y adalah posisi Top-Left dari item di Preview
            # Kita sesuaikan pivot ke tengah teks
            painter.translate(x + (text_w*scale)/2, y + (text_h*scale)/2)
            painter.rotate(rotation)
            painter.scale(scale, scale)
            painter.setOpacity(opacity)
            
            # Gambar Teks
            # y offset sedikit digeser ke bawah karena drawText menggambar dari baseline
            painter.drawText(-text_w/2, text_h/4, text_content)

        painter.restore()

    def _mix_audio(self, output_path):
        # ... (Kode _mix_audio SAMA PERSIS dengan sebelumnya, tidak perlu diubah) ...
        # Pastikan Anda menyalin method _mix_audio dari file sebelumnya ke sini
        if hasattr(self.timeline, 'layers'): # Support method property baru
             all_layers = self.timeline.layers
        else:
             all_layers = self.timeline._layers

        audio_layers = []
        for l in all_layers:
            if l.type in ['video', 'audio'] and l.payload.get('path'):
                audio_layers.append(l)
        
        if not audio_layers: return False

        cmd = ['ffmpeg', '-y']
        filter_complex = []
        mix_inputs = []
        
        for layer in audio_layers:
            cmd.extend(['-i', layer.payload['path']])
            
        for i, layer in enumerate(audio_layers):
            start_ms = int(layer.time.start * 1000)
            if start_ms > 0:
                tag = f"d{i}"
                filter_complex.append(f"[{i}:a]adelay={start_ms}|{start_ms}[{tag}]")
                mix_inputs.append(f"[{tag}]")
            else:
                mix_inputs.append(f"[{i}:a]")
        
        inputs_count = len(mix_inputs)
        inputs_str = "".join(mix_inputs)
        filter_complex.append(f"{inputs_str}amix=inputs={inputs_count}:dropout_transition=0[out]")
        
        cmd.extend(['-filter_complex', ";".join(filter_complex)])
        cmd.extend(['-map', '[out]', '-c:a', 'aac', '-b:a', '192k', output_path])
        
        creation_flags = 0
        if os.name == 'nt': creation_flags = subprocess.CREATE_NO_WINDOW
            
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creation_flags)
        return result.returncode == 0