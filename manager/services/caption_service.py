# manager/services/caption_service.py
import uuid
import time # Untuk simulasi delay
from PySide6.QtCore import QObject, QThread, Signal
from manager.project_state import LayerData

# Nanti import engine asli: 
# from engine.caption.transcriber import assembly_transcribe

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
            print(f"[WORKER] Starting AI Job for: {self.audio_path}")
            
            # SIMULASI DELAY (Agar terlihat efek async-nya di UI)
            # TODO: Nanti ganti dengan real processing time
            time.sleep(2) 
            
            # MOCK DATA
            mock_segments = [
                {"text": "Halo semuanya", "start": 0.5, "end": 2.0},
                {"text": "Selamat datang di", "start": 2.1, "end": 3.5},
                {"text": "Tutorial MamenPro", "start": 3.6, "end": 5.0},
                {"text": "Mode Async Keren!", "start": 5.1, "end": 7.0}
            ]
            
            new_layers = []
            for i, seg in enumerate(mock_segments):
                # [DEBT NOTE #2] Z-index ditentukan di sini (Hardcoded).
                # IDEALNYA: Worker tidak tahu z-index. Controller yang set nanti.
                layer_id = str(uuid.uuid4())[:8]
                layer = LayerData(
                    id=layer_id,
                    type="text",
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

class CaptionService(QObject):
    """
    Manager yang mengatur Worker Thread.
    Jembatan antara Editor dan AI Engine.
    """
    # Signal Relay (Meneruskan dari Worker ke Controller)
    sig_success = Signal(list)
    sig_fail = Signal(str)

    def __init__(self):
        super().__init__()
        self.worker = None

    def start_generate_async(self, audio_path: str, config: dict):
        """
        Memulai proses captioning di thread terpisah.
        """
        # [DEBT NOTE #1] Terminate adalah darurat.
        # BAHAYA: Resource bisa bocor.
        # TODO: Implementasi graceful cancellation (requestInterruption)
        if self.worker and self.worker.isRunning():
            print("[SERVICE] ⚠️ Terminating running worker forcefullly (DEBT)")
            self.worker.terminate()
            self.worker.wait() # Tunggu sampai benar-benar mati
            
        # Siapkan Worker Baru
        self.worker = CaptionWorker(audio_path, config)
        
        # Sambungkan Kabel Signal
        self.worker.sig_finished.connect(self._on_worker_finished)
        self.worker.sig_error.connect(self.sig_fail)
        
        # Jalankan!
        self.worker.start()
        
    def _on_worker_finished(self, layers):
        self.sig_success.emit(layers)