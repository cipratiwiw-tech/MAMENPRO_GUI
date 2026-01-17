# manager/services/caption_service.py
import uuid
import time
from PySide6.QtCore import QObject, QThread, Signal

# IMPORT DATA MODEL BARU
from manager.timeline.layer_model import LayerModel
from manager.timeline.time_range import TimeRange

# IMPORT ENGINE ASLI (Bisa di-uncomment jika API Key sudah siap)
# from engine.caption.transcriber import assembly_transcribe, assembly_upload

class CaptionWorker(QThread):
    """
    Worker Thread yang mengubah Audio -> List of LayerModel.
    Tidak ada rendering visual di sini.
    """
    # Signal mengirim list[LayerModel] ke Controller
    sig_finished = Signal(list) 
    sig_error = Signal(str)

    def __init__(self, audio_path, config):
        super().__init__()
        self.audio_path = audio_path
        self.config = config

    def run(self):
        try:
            # 1. --- PROSES BERAT (AI) ---
            # Idealnya memanggil engine transcriber di sini.
            # Untuk stabilitas langkah ini, kita gunakan Simulasi Data yang AKURAT secara struktur.
            
            # [SIMULASI AI START]
            time.sleep(1.5) # Simulasi latency network
            
            # Raw Data: Hasil murni dari Transcriber (seperti AssemblyAI / Whisper)
            # Format: {'text': string, 'start': float (sec), 'end': float (sec)}
            raw_segments = [
                {"text": "Halo selamat datang", "start": 0.5, "end": 2.0},
                {"text": "Di tutorial MamenPro", "start": 2.1, "end": 3.5},
                {"text": "Editor video Python", "start": 3.6, "end": 5.0},
                {"text": "Yang arsitekturnya rapi", "start": 5.1, "end": 7.0}
            ]
            # [SIMULASI AI END]
            
            # 2. --- DATA MAPPING (Raw -> LayerModel) ---
            results = []
            
            # Ambil config style dari UI (jika ada), atau default
            style_payload = {
                "font_family": self.config.get("font_family", "Arial"),
                "font_size": self.config.get("font_size", 40),
                "text_color": self.config.get("text_color", "#ffffff"),
                "is_bold": True
            }

            for seg in raw_segments:
                # Generate ID unik untuk setiap potongan caption
                layer_id = str(uuid.uuid4())[:8]
                
                # Buat Model Waktu
                # Pastikan end > start
                start_t = float(seg["start"])
                end_t = float(seg["end"])
                if end_t <= start_t: end_t = start_t + 1.0

                # Buat Payload (Gabungan Teks + Style)
                payload = style_payload.copy()
                payload["text_content"] = seg["text"]

                # Buat LayerModel
                # Tipe 'caption' atau 'text' (tergantung renderer Anda nanti)
                model = LayerModel(
                    id=layer_id,
                    type="text", 
                    time=TimeRange(start_t, end_t),
                    z_index=10, # Caption biasanya di atas (Z-Index tinggi)
                    payload=payload
                )
                
                results.append(model)
            
            # 3. --- SELESAI ---
            self.sig_finished.emit(results)
            
        except Exception as e:
            self.sig_error.emit(str(e))

class CaptionService(QObject):
    """
    Manager Service.
    Jembatan Controller <-> Worker.
    """
    sig_success = Signal(list) # meneruskan list[LayerModel]
    sig_fail = Signal(str)

    def __init__(self):
        super().__init__()
        self.worker = None

    def start_generate_async(self, audio_path: str, config: dict):
        # Matikan worker lama jika masih jalan (Clean up)
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        # Setup Worker Baru
        self.worker = CaptionWorker(audio_path, config)
        self.worker.sig_finished.connect(self.sig_success)
        self.worker.sig_error.connect(self.sig_fail)
        
        # Jalankan
        self.worker.start()