import time
import gc
import os
from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtGui import QImage 

from engine.compositor import Compositor
from engine.ffmpeg_renderer import FFmpegRenderer
from engine.video_service import VideoService
from manager.timeline.timeline_engine import TimelineEngine

class RenderWorker(QThread):
    sig_progress = Signal(int)
    sig_finished = Signal(bool, str)
    sig_log = Signal(str)

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
        render_vs = VideoService()
        renderer = None
        
        try:
            # 1. ANALISA AUDIO (SINGLE TRACK)
            # Cari layer pertama yang punya potensi suara (video/audio)
            audio_path = None
            audio_delay_ms = 0
            
            # Akses private member _layers (ini shortcut aman karena kita di worker copy)
            # Sebaiknya timeline_engine punya method public, tapi untuk sekarang ok.
            all_layers = self.timeline._layers 
            
            for layer in all_layers:
                if layer.type in ["video", "audio"]:
                    # Ambil path dari payload
                    path = layer.payload.get("path")
                    if path and os.path.exists(path):
                        audio_path = path
                        # Hitung delay (start_time * 1000)
                        start_time = layer.time.start
                        audio_delay_ms = int(start_time * 1000)
                        
                        self.sig_log.emit(f"🎤 Audio Source: {os.path.basename(path)} (Delay: {audio_delay_ms}ms)")
                        break # HANYA 1 TRACK SESUAI JANJI

            # 2. SETUP RENDERER
            compositor = Compositor(render_vs, self.width, self.height)
            renderer = FFmpegRenderer(self.output_path, self.width, self.height, self.fps)
            
            # Start process DENGAN AUDIO CONFIG
            renderer.start_process(audio_path=audio_path, audio_delay_ms=audio_delay_ms)
            
            total_duration = self.timeline.get_total_duration()
            if total_duration <= 0: total_duration = 1.0
            
            total_frames = int(total_duration * self.fps)
            self.sig_log.emit(f"Rendering {total_frames} frames...")

            # 3. RENDER LOOP (Sama seperti sebelumnya)
            for frame_idx in range(total_frames):
                if self.is_cancelled:
                    self.sig_log.emit("⚠️ Render Cancelled")
                    break
                
                current_time = frame_idx / self.fps
                
                # A. Rendering Visual
                active_layers = self.timeline.get_active_layers(current_time)
                qimage = compositor.compose_frame(current_time, active_layers)
                
                if qimage.isNull(): continue 

                qimage_rgb = qimage.convertToFormat(QImage.Format_RGB888)
                ptr = qimage_rgb.constBits()
                if ptr:
                    renderer.write_frame(ptr.tobytes())
                
                # B. Progress
                if frame_idx % 10 == 0:
                    pct = int((frame_idx / total_frames) * 100)
                    self.sig_progress.emit(pct)

            if self.is_cancelled:
                self.sig_finished.emit(False, "Cancelled")
            else:
                self.sig_finished.emit(True, self.output_path)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.sig_finished.emit(False, str(e))
            
        finally:
            self.sig_log.emit("🧹 Cleaning up...")
            if renderer: renderer.close_process()
            render_vs.release_all()
            gc.collect()
            
            self.quit()   # ⬅️ beri sinyal ke Qt event loop

# Class RenderService tetap sama, tidak perlu diubah
class RenderService(QObject):
    def __init__(self):
        super().__init__()
        self.worker = None

    def start_render_process(self, timeline_engine, config):
        output_path = config.get("path")
        if self.worker and self.worker.isRunning():
            return False, "Render sedang berjalan"

        self.worker = RenderWorker(timeline_engine, output_path, config)
        return True, self.worker