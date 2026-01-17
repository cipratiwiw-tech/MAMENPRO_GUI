import time
import gc
from PySide6.QtCore import QThread, Signal, QObject
# 👇👇👇 PASTIKAN BARIS INI ADA! 👇👇👇
from PySide6.QtGui import QImage 

from engine.compositor import Compositor
from engine.ffmpeg_renderer import FFmpegRenderer
from engine.video_service import VideoService
from manager.timeline.timeline_engine import TimelineEngine

class RenderWorker(QThread):
    sig_progress = Signal(int)       # 0-100%
    sig_finished = Signal(bool, str) # Success, Message
    sig_log = Signal(str)            # Log process

    def __init__(self, timeline_engine: TimelineEngine, output_path: str, config: dict):
        super().__init__()
        self.timeline = timeline_engine 
        self.output_path = output_path
        self.config = config
        
        self.fps = config.get("fps", 30)
        self.width = config.get("width", 1920)
        self.height = config.get("height", 1080)
        
        self.is_cancelled = False

    def run(self):
        # Gunakan instance VideoService baru (Private) agar tidak ganggu Preview
        render_vs = VideoService()
        renderer = None
        
        try:
            # 1. SETUP
            compositor = Compositor(render_vs, self.width, self.height)
            renderer = FFmpegRenderer(self.output_path, self.width, self.height, self.fps)
            renderer.start_process()
            
            total_duration = self.timeline.get_total_duration()
            # Safety: Render minimal 1 detik jika kosong
            if total_duration <= 0: total_duration = 1.0
            
            total_frames = int(total_duration * self.fps)
            self.sig_log.emit(f"Rendering {total_frames} frames ({self.width}x{self.height} @ {self.fps}fps)...")

            # 2. RENDER LOOP
            for frame_idx in range(total_frames):
                if self.is_cancelled:
                    self.sig_log.emit("⚠️ Render Cancelled by User")
                    break
                
                # Hitung waktu presisi
                current_time = frame_idx / self.fps
                
                # A. Rendering
                active_layers = self.timeline.get_active_layers(current_time)
                qimage = compositor.compose_frame(current_time, active_layers)
                
                # B. Convert & Write ke FFmpeg
                if qimage.isNull(): 
                    continue 

                # Konversi ke RGB888 (24-bit) menggunakan Enum QImage
                qimage_rgb = qimage.convertToFormat(QImage.Format_RGB888)
                ptr = qimage_rgb.constBits()
                if ptr:
                    raw_bytes = ptr.tobytes()
                    renderer.write_frame(raw_bytes)
                
                # C. Progress
                if frame_idx % 10 == 0:
                    pct = int((frame_idx / total_frames) * 100)
                    self.sig_progress.emit(pct)
                    
                # D. Garbage Collection (Opsional)
                # if frame_idx % 200 == 0: gc.collect() 

            if self.is_cancelled:
                self.sig_finished.emit(False, "Cancelled")
            else:
                self.sig_finished.emit(True, self.output_path)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.sig_finished.emit(False, str(e))
            
        finally:
            # 3. CLEANUP RESOURCES
            self.sig_log.emit("🧹 Cleaning up resources...")
            if renderer:
                renderer.close_process()
            
            # Lepas akses file video
            render_vs.release_all()
            
            # Paksa bersihkan RAM
            gc.collect()

class RenderService(QObject):
    """Manager Service untuk Render"""
    def __init__(self):
        super().__init__()
        self.worker = None

    def start_render_process(self, timeline_engine, config):
        output_path = config.get("path")
        
        if self.worker and self.worker.isRunning():
            return False, "Render sedang berjalan"

        self.worker = RenderWorker(timeline_engine, output_path, config)
        return True, self.worker