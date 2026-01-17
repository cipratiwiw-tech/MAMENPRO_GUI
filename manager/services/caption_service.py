# manager/services/caption_service.py
import uuid
import time
from PySide6.QtCore import QObject, QThread, Signal
from manager.project_state import LayerData

# Nanti import engine asli: 
# from engine.caption.transcriber import Transcriber

class CaptionWorker(QThread):
    """
    Worker: Kuli panggul yang bekerja di background.
    """
    sig_finished = Signal(list) # Mengirim hasil (list of layers) ke Service
    sig_error = Signal(str)

    def __init__(self, audio_path, config):
        super().__init__()
        self.audio_path = audio_path
        self.config = config

    def run(self):
        try:
            print(f"[WORKER] Starting AI Job for: {self.audio_path}")
            
            # --- SIMULASI PROSES BERAT ---
            # Di real app, ini adalah proses upload & transcribe yang memakan waktu 10-60 detik.
            # Kita pakai sleep agar terasa efek 'Loading'-nya di UI.
            time.sleep(2.0) 
            
            # --- MOCK RESULT ---
            mock_segments = [
                {"text": "Halo semuanya", "start": 0.5, "end": 2.0},
                {"text": "Selamat datang di", "start": 2.1, "end": 3.5},
                {"text": "Tutorial MamenPro", "start": 3.6, "end": 5.0},
                {"text": "Jangan lupa subscribe", "start": 5.1, "end": 7.0}
            ]
            
            new_layers = []
            for i, seg in enumerate(mock_segments):
                layer_id = str(uuid.uuid4())[:8]
                
                # [DEBT] Z-Index sementara di-hardcode disini.
                # Nanti idealnya Controller yang mengatur stacking order final.
                layer = LayerData(
                    id=layer_id,
                    type="text",
                    name=f"Sub {i+1}: {seg['text'][:10]}...",
                    properties={
                        "text_content": seg["text"],
                        "start_time": seg["start"],
                        "duration": seg["end"] - seg["start"],
                        "y": 800, # Posisi bawah
                        "font_size": 50,
                        "text_color": "#ffff00",
                        "is_bold": True
                    },
                    z_index=100 + i 
                )
                new_layers.append(layer)
            
            # Pekerjaan selesai, lapor ke mandor (Service)
            self.sig_finished.emit(new_layers)
            
        except Exception as e:
            self.sig_error.emit(str(e))

class CaptionService(QObject):
    """
    Service: Mandor yang mengatur Worker.
    Controller bicara ke sini, bukan langsung ke thread.
    """
    # Signal Relay (Meneruskan dari Worker ke Controller)
    sig_success = Signal(list)
    sig_fail = Signal(str)

    def __init__(self):
        super().__init__()
        self.worker = None

    def start_generate_async(self, audio_path: str, config: dict):
        """
        Memulai proses captioning tanpa memblokir UI.
        """
        # [CATATAN SAFETY] 
        # Mematikan thread paksa (terminate) sebenarnya berbahaya untuk jangka panjang (memory leak).
        # Tapi untuk fase dev awal ini, kita pastikan tidak ada double worker yang jalan.
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        # Siapkan Worker Baru
        self.worker = CaptionWorker(audio_path, config)
        
        # Sambungkan Kabel
        self.worker.sig_finished.connect(self._on_worker_finished)
        self.worker.sig_error.connect(self.sig_fail)
        
        # Jalankan
        self.worker.start()
        
    def _on_worker_finished(self, layers):
        # Bersih-bersih worker
        self.worker = None
        # Teruskan data ke Controller
        self.sig_success.emit(layers)