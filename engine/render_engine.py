# engine/render_engine.py
import cv2
import numpy as np
import subprocess
import os
import tempfile
from PySide6.QtGui import QImage, QPainter, QColor, QFont, QPen, QFontMetrics
from PySide6.QtCore import Qt

from engine.ffmpeg_renderer import FFmpegRenderer
from engine.chroma_processor import ChromaProcessor

class RenderEngine:
    def __init__(self, timeline, video_service):
        self.timeline = timeline
        self.video_service = video_service
        self.renderer = None 

    def render(self, output_path, settings, callback=None):
        fps = settings.get("fps", 30)
        width = settings.get("width", 1080)
        height = settings.get("height", 1920)
        
        duration = self.timeline.get_total_duration()
        total_frames = int(duration * fps)
        if total_frames == 0: total_frames = 1
                
        print("🔊 Processing Audio Mix...")
        temp_audio_path = os.path.join(tempfile.gettempdir(), "mamen_mix_temp.aac")
        has_audio = self._mix_audio(temp_audio_path)

        print(f"[RENDER] Init FFmpeg: {width}x{height} @ {fps}fps")
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
                
                canvas = QImage(width, height, QImage.Format_ARGB32)
                canvas.fill(QColor(0, 0, 0, 255)) 
                painter = QPainter(canvas)
                
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                
                for layer in active_layers:
                    self._draw_layer(painter, layer, current_time)
                
                painter.end()
                
                rgb_image = canvas.convertToFormat(QImage.Format_RGB888)
                raw_bytes = rgb_image.constBits().tobytes()
                self.renderer.write_frame(raw_bytes)
                
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

    def _draw_layer(self, painter, layer, global_time):
        props = layer.payload
        layer_type = layer.type
        
        x = float(props.get("x", 0))
        y = float(props.get("y", 0))
        scale = float(props.get("scale", 100)) / 100.0
        rotation = float(props.get("rotation", 0))
        opacity = float(props.get("opacity", 1.0))
        
        painter.save()
        
        if layer_type in ['video', 'image']:
            path = props.get("path")
            if path:
                start_offset = float(props.get("start_time", 0.0))
                local_time = global_time - start_offset
                
                render_props = {
                    "color": {
                        "brightness": props.get("brightness", 0),
                        "contrast": props.get("contrast", 0),
                        "saturation": props.get("saturation", 0),
                        "hue": props.get("hue", 0),
                        "temperature": props.get("temperature", 0),
                    },
                    "effect": {
                        "blur": props.get("blur", 0),
                        "vignette": props.get("vignette", 0),
                    }
                }
                
                qimg = self.video_service.get_frame(layer.id, local_time, render_props)
                
                if not qimg.isNull():
                    if props.get("chroma_active", False):
                        c_color = props.get("chroma_color", "#00ff00")
                        c_thresh = float(props.get("chroma_threshold", 0.15))
                        qimg = ChromaProcessor.process_qimage(qimg, c_color, c_thresh)
                    
                    w, h = qimg.width(), qimg.height()
                    
                    # [PERBAIKAN POSISI]
                    # Gunakan w/2 dan h/2 (TANPA scale) agar pivot point konsisten 
                    # dengan QGraphicsItem di preview.
                    painter.translate(x + w/2, y + h/2)
                    
                    painter.rotate(rotation)
                    painter.scale(scale, scale)
                    painter.setOpacity(opacity)
                    
                    # Draw image centered at (0,0) local coord
                    painter.drawImage(-w/2, -h/2, qimg)

        elif layer_type in ['text', 'caption']:
            # ... (kode text biarkan sama, atau sesuaikan pivotnya jika perlu)
            text = props.get("text_content", "Text")
            font = QFont(props.get("font_family", "Arial"), int(props.get("font_size", 60)))
            if props.get("is_bold"): font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(props.get("text_color", "#ffffff")))
            
            fm = QFontMetrics(font)
            rect = fm.boundingRect(text)
            text_w, text_h = rect.width(), rect.height()
            
            # Text biasanya pivotnya center juga agar rotasi aman
            painter.translate(x + text_w/2, y + text_h/2)
            painter.rotate(rotation)
            painter.scale(scale, scale)
            painter.setOpacity(opacity)
            painter.drawText(-text_w/2, text_h/4, text)

        painter.restore()

    def _mix_audio(self, output_path):
        if hasattr(self.timeline, 'layers'): all_layers = self.timeline.layers
        else: all_layers = self.timeline._layers
        
        audio_layers = [l for l in all_layers if l.type in ['video', 'audio'] and l.payload.get('path')]
        if not audio_layers: return False

        cmd = ['ffmpeg', '-y']
        filter_complex = []
        mix_inputs = []
        for l in audio_layers: cmd.extend(['-i', l.payload['path']])
        for i, l in enumerate(audio_layers):
            start = int(l.time.start * 1000)
            tag = f"d{i}" if start > 0 else f"{i}:a"
            if start > 0:
                filter_complex.append(f"[{i}:a]adelay={start}|{start}[{tag}]")
                mix_inputs.append(f"[{tag}]")
            else:
                mix_inputs.append(tag)
        
        inputs_str = "".join(mix_inputs)
        filter_complex.append(f"{inputs_str}amix=inputs={len(mix_inputs)}:dropout_transition=0[out]")
        
        cmd.extend(['-filter_complex', ";".join(filter_complex), '-map', '[out]', '-c:a', 'aac', '-b:a', '192k', output_path])
        
        creation_flags = 0
        if os.name == 'nt': creation_flags = subprocess.CREATE_NO_WINDOW
        
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creation_flags)
        return True