# manager/services/render_service.py
import threading
from PySide6.QtCore import QObject, Signal, QThread
from engine.render_engine import RenderEngine

class RenderWorker(QObject):
    sig_progress = Signal(int)
    sig_finished = Signal(bool, str) # Success, Message

    def __init__(self, timeline, settings, video_service):
        super().__init__()
        self.timeline = timeline
        self.settings = settings
        self.video_service = video_service
        self.engine = None
        self._is_cancelled = False

    def run(self):
        try:
            # ✅ PERBAIKAN: Kirim timeline & video_service ke RenderEngine
            self.engine = RenderEngine(self.timeline, self.video_service) 
            
            output_path = self.settings.get("output_path", "output.mp4")
            
            def progress_callback(p):
                if self._is_cancelled: raise Exception("Cancelled")
                self.sig_progress.emit(int(p))

            self.engine.render(
                output_path, 
                self.settings, 
                callback=progress_callback
            )
            
            self.sig_finished.emit(True, output_path)
            
        except Exception as e:
            msg = str(e)
            if msg == "Cancelled":
                self.sig_finished.emit(False, "Render Cancelled")
            else:
                self.sig_finished.emit(False, f"Error: {msg}")

    def stop(self):
        self._is_cancelled = True
        if self.engine:
            self.engine.stop()

class RenderService(QObject):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None

    def start_render_process(self, timeline, settings, video_service):
        """
        Memulai proses render di thread terpisah.
        Mengembalikan: (Success: bool, Worker/Message)
        """
        # Cek apakah sedang render
        if self.thread and self.thread.isRunning():
            return False, "Render already in progress"

        # 1. Setup Thread & Worker
        self.thread = QThread()
        self.worker = RenderWorker(timeline, settings, video_service)
        self.worker.moveToThread(self.thread)

        # 2. Wiring
        self.thread.started.connect(self.worker.run)
        
        # Cleanup otomatis
        self.worker.sig_finished.connect(self.thread.quit)
        self.worker.sig_finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        # Bersihkan referensi self saat selesai
        self.thread.finished.connect(self._reset_state)

        # 3. Start
        self.thread.start()
        return True, self.worker

    def _reset_state(self):
        self.thread = None
        self.worker = None