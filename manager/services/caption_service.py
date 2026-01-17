# manager/services/caption_service.py
import uuid
from manager.project_state import LayerData

# Nanti import engine asli: 
# from engine.caption.transcriber import Transcriber
# Untuk sekarang kita MOCK agar aplikasi bisa jalan tanpa install library AI berat

class CaptionService:
    """
    Jembatan antara Editor dan AI Engine.
    Mengubah Audio -> List of Text Layers.
    """

    def generate_layers_from_audio(self, audio_path: str, config: dict) -> list[LayerData]:
        """
        Menerima path audio, mengembalikan banyak layer teks.
        """
        print(f"[CAPTION SERVICE] Transcribing: {audio_path} | Config: {config}")
        
        # --- SIMULASI HASIL AI (MOCK) ---
        # Di kode asli: result = Transcriber.transcribe(audio_path, config)
        
        mock_segments = [
            {"text": "Halo semuanya", "start": 0.5, "end": 2.0},
            {"text": "Selamat datang di", "start": 2.1, "end": 3.5},
            {"text": "Tutorial MamenPro", "start": 3.6, "end": 5.0},
            {"text": "Jangan lupa subscribe", "start": 5.1, "end": 7.0}
        ]
        
        new_layers = []
        for i, seg in enumerate(mock_segments):
            # Buat ID unik
            layer_id = str(uuid.uuid4())[:8]
            
            # Buat LayerData Teks
            layer = LayerData(
                id=layer_id,
                type="text",
                name=f"Sub {i+1}: {seg['text'][:10]}...",
                properties={
                    "text_content": seg["text"],
                    "start_time": seg["start"],
                    "duration": seg["end"] - seg["start"],
                    "y": 600, # Posisi bawah (subtitle)
                    "font_size": 40,
                    "text_color": "#ffff00", # Kuning standar sub
                    "is_bold": True
                },
                z_index=100 + i # Pastikan di atas layer video
            )
            new_layers.append(layer)
            
        return new_layers