import time
from PySide6.QtCore import QThread, Signal, QObject

from engine.compositor import Compositor
from engine.ffmpeg_renderer import FFmpegRenderer
from manager.timeline.timeline_engine import TimelineEngine
from engine.video_service import VideoService # Import Class nya saja

class RenderWorker(QThread):
    sig_progress = Signal(int)       # 0-100%
    sig_finished = Signal(bool, str) # Success, Message
    sig_log = Signal(str)            # Log process

    def __init__(self, timeline_engine: TimelineEngine, output_path: str, config: dict):
        super().__init__()
        # Kita copy referensi engine. 
        # Karena TimelineEngine hanya READ (get_active_layers) saat render, ini aman.
        self.timeline = timeline_engine 
        self.output_path = output_path
        self.config = config
        
        self.fps = config.get("fps", 30)
        self.width = config.get("width", 1920)
        self.height = config.get("height", 1080)
        
        self.is_cancelled = False

    def run(self):
        # 1. INSTANCE PRIVATE (Video Service Khusus Render)
        # Ini menjamin tidak ada konflik dengan Preview UI
        render_vs = VideoService()
        
        try:
            # 2. Setup Compositor dengan Provider Private
            compositor = Compositor(render_vs, self.width, self.height)
            renderer = FFmpegRenderer(self.output_path, self.width, self.height, self.fps)
            renderer.start_process()
            
            total_duration = self.timeline.get_total_duration()
            total_frames = int(total_duration * self.fps)
            
            self.sig_log.emit(f"Rendering {total_frames} frames...")

            # 3. LOOPING PRESISI (Based on Frame Count)
            for frame_idx in range(total_frames):
                if self.is_cancelled: break
                
                # Hitung waktu berdasarkan frame number (Lebih akurat dari float addition)
                current_time = frame_idx / self.fps
                
                # A. Get Active Layers
                active_layers = self.timeline.get_active_layers(current_time)
                
                # B. Compose (Pake QImage)
                qimage = compositor.compose_frame(current_time, active_layers)
                
                # C. Konversi ke RGB24 Raw Bytes
                # Convert ke RGB888 (24-bit RGB) -> Sesuai -pix_fmt rgb24 di FFmpeg
                qimage_rgb = qimage.convertToFormat(QImage.Format_RGB888)
                raw_bytes = qimage_rgb.constBits().tobytes()
                
                renderer.write_frame(raw_bytes)
                
                # D. Progress
                if frame_idx % 10 == 0:
                    pct = int((frame_idx / total_frames) * 100)
                    self.sig_progress.emit(pct)

            renderer.close_process()
            self.sig_finished.emit(True, self.output_path)

        except Exception as e:
            self.sig_finished.emit(False, str(e))
        finally:
            # PENTING: Lepaskan file handle video di thread ini
            render_vs.release_all()

class RenderService(QObject):
    """Manager Service untuk Render"""
    def __init__(self):
        super().__init__()
        self.worker = None

    def start_render_process(self, timeline_engine, config):
        # Config example: {'path': 'out.mp4', 'width': 1920, 'height': 1080, 'fps': 30}
        output_path = config.get("path")
        
        if self.worker and self.worker.isRunning():
            return False, "Render sedang berjalan"

        self.worker = RenderWorker(timeline_engine, output_path, config)
        return True, self.worker # Return worker untuk di-connect signalnya oleh Controller