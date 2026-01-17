# manager/services/caption_service.py
import uuid
from PySide6.QtCore import QObject, QThread, Signal
from manager.project_state import LayerData

# Worker Thread: Buruh yang bekerja di latar belakang
class CaptionWorker(QThread):
    sig_finished = Signal(list) # Mengirim hasil (list of layers)
    sig_error = Signal(str)

    def __init__(self, audio_path, config):
        super().__init__()
        self.audio_path = audio_path
        self.config = config

    def run(self):
        try:
            # --- DISINI LOGIC BERAT (AI) BERJALAN ---
            # Di masa depan, import Transcriber asli di sini.
            # from engine.caption.transcriber import assembly_transcribe
            
            print(f"[WORKER] Starting AI Job for: {self.audio_path}")
            
            # SIMULASI DELAY (Agar terlihat efek async-nya)
            import time
            time.sleep(2) 
            
            # MOCK DATA (Sama seperti logic lamamu)
            mock_segments = [
                {"text": "Halo semuanya", "start": 0.5, "end": 2.0},
                {"text": "Selamat datang di", "start": 2.1, "end": 3.5},
                {"text": "Tutorial MamenPro", "start": 3.6, "end": 5.0},
                {"text": "Mode Async Keren!", "start": 5.1, "end": 7.0}
            ]
            
            new_layers = []
            for i, seg in enumerate(mock_segments):
                # Catatan #2: Z-index masih hardcoded disini, nanti kita refactor di Controller
                layer_id = str(uuid.uuid4())[:8]
                layer = LayerData(
                    id=layer_id,
                    type="text", # Catatan #3: Tetap konsisten sebagai Text Layer
                    name=f"Sub {i+1}",
                    properties={
                        "text_content": seg["text"],
                        "start_time": seg["start"],
                        "duration": seg["end"] - seg["start"],
                        "y": 800, 
                        "font_size": 50,
                        "text_color": "#ffff00",
                        "is_bold": True
                    },
                    z_index=100 + i 
                )
                new_layers.append(layer)
            
            # Kirim hasil ke Main Thread
            self.sig_finished.emit(new_layers)
            
        except Exception as e:
            self.sig_error.emit(str(e))

class CaptionService(QObject): # Inherit QObject agar bisa handle signal
    """
    Manager yang mengatur Worker Thread.
    """
    # Signal Relay (Meneruskan dari Worker ke Controller)
    sig_success = Signal(list)
    sig_fail = Signal(str)

    def __init__(self):
        super().__init__()
        self.worker = None

    def start_generate_async(self, audio_path: str, config: dict):
        # Hentikan worker lama jika masih jalan (opsional)
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            
        # Siapkan Worker Baru
        self.worker = CaptionWorker(audio_path, config)
        
        # Sambungkan Kabel Signal
        self.worker.sig_finished.connect(self._on_worker_finished)
        self.worker.sig_error.connect(self.sig_fail)
        
        # Jalankan!
        self.worker.start()
        
    def _on_worker_finished(self, layers):
        self.sig_success.emit(layers)