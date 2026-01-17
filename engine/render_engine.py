# engine/render_engine.py
import cv2
import numpy as np
import subprocess
import os
import tempfile
from PySide6.QtGui import QImage, QPainter, QColor

from engine.ffmpeg_renderer import FFmpegRenderer

class RenderEngine:
    def __init__(self, timeline, video_service):
        self.timeline = timeline
        self.video_service = video_service
        self.renderer = None 

    def render(self, output_path, settings, callback=None):
        fps = settings.get("fps", 30)
        duration = self.timeline.get_total_duration()
        total_frames = int(duration * fps)
        width, height = 1920, 1080 
        
        # 1. AUDIO PROCESSING
        print("🔊 Processing Audio Mix...")
        temp_audio_path = os.path.join(tempfile.gettempdir(), "mamen_mix_temp.aac")
        
        # Coba mix audio, hasilnya True/False
        has_audio = self._mix_audio(temp_audio_path)
        
        if has_audio:
            print(f"✅ Audio Mix Created: {temp_audio_path}")
        else:
            print("⚠️ Rendering Silent Video (No Audio Sources Found)")

        # 2. INIT RENDERER
        self.renderer = FFmpegRenderer(output_path, width, height, fps)
        
        # Kirim path audio yang sudah di-mix (jika ada)
        if has_audio:
            # start_process(audio_path, delay=0) karena delay sudah di-handle saat mixing
            self.renderer.start_process(audio_path=temp_audio_path, audio_delay_ms=0)
        else:
            self.renderer.start_process() 

        try:
            for frame_idx in range(total_frames):
                current_time = frame_idx / float(fps)
                
                # A. Layer Management
                active_layers = self.timeline.get_active_layers(current_time)
                active_layers.sort(key=lambda x: x.z_index)
                
                # B. Canvas Setup
                canvas = QImage(width, height, QImage.Format_ARGB32)
                canvas.fill(QColor(0, 0, 0, 0)) 
                painter = QPainter(canvas)
                
                # C. Drawing Loop
                for layer in active_layers:
                    layer_path = layer.payload.get("path")
                    if layer_path:
                        local_time = current_time - layer.time.start
                        img = self.video_service.get_frame_image(layer_path, local_time)
                        
                        if img and not img.isNull():
                            props = layer.payload
                            x = props.get("x", 0)
                            y = props.get("y", 0)
                            scale = props.get("scale", 100) / 100.0
                            rotation = props.get("rotation", 0)
                            opacity = props.get("opacity", 1.0)
                            
                            painter.save()
                            painter.translate(x + img.width()/2, y + img.height()/2)
                            painter.rotate(rotation)
                            painter.scale(scale, scale)
                            painter.setOpacity(opacity)
                            painter.drawImage(-img.width()/2, -img.height()/2, img)
                            painter.restore()
                
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
            raise e
            
        finally:
            if self.renderer:
                self.renderer.close_process()
                self.renderer = None
            
            # Cleanup temp audio
            if has_audio and os.path.exists(temp_audio_path):
                try: os.remove(temp_audio_path)
                except: pass

    def _mix_audio(self, output_path):
        """
        Menggabungkan audio dari semua layer menggunakan FFmpeg.
        """
        # AKSES LAYERS YANG ROBUST (Cek property 'layers', lalu fallback '_layers')
        if hasattr(self.timeline, 'layers'):
            all_layers = self.timeline.layers
        elif hasattr(self.timeline, '_layers'):
            all_layers = self.timeline._layers
        else:
            print("❌ Audio Mix Error: Timeline layers not accessible!")
            return False
            
        audio_layers = []
        for l in all_layers:
            # Filter hanya layer Video/Audio yang punya Path
            if l.type in ['video', 'audio'] and l.payload.get('path'):
                audio_layers.append(l)
        
        if not audio_layers:
            print("ℹ️ Info: No audio/video layers to mix.")
            return False

        # Bangun Command FFmpeg
        cmd = ['ffmpeg', '-y']
        filter_complex = []
        mix_inputs = []
        
        # 1. Inputs
        for layer in audio_layers:
            cmd.extend(['-i', layer.payload['path']])
            
        # 2. Filter Graph (Delay & Mix)
        for i, layer in enumerate(audio_layers):
            start_ms = int(layer.time.start * 1000)
            
            # Jika ada delay (posisi di timeline > 0)
            if start_ms > 0:
                tag = f"d{i}"
                filter_complex.append(f"[{i}:a]adelay={start_ms}|{start_ms}[{tag}]")
                mix_inputs.append(f"[{tag}]")
            else:
                mix_inputs.append(f"[{i}:a]")
        
        # Mix semua stream
        inputs_count = len(mix_inputs)
        inputs_str = "".join(mix_inputs)
        
        # Gunakan amix
        filter_complex.append(f"{inputs_str}amix=inputs={inputs_count}:dropout_transition=0[out]")
        
        cmd.extend(['-filter_complex', ";".join(filter_complex)])
        cmd.extend(['-map', '[out]', '-c:a', 'aac', '-b:a', '192k', output_path])
        
        # Debug Command (Cek log ini jika audio masih hilang)
        # print(f"🎵 Mixing Cmd: {' '.join(cmd)}")
        
        # Jalankan FFmpeg
        creation_flags = 0
        if os.name == 'nt':
            creation_flags = subprocess.CREATE_NO_WINDOW
            
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            creationflags=creation_flags
        )
        
        if result.returncode != 0:
            print("❌ Audio Mix Failed:", result.stderr.decode())
            return False
            
        return True