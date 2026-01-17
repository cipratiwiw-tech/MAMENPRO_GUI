# manager/services/render_service.py
import os

class RenderService:
    """
    Service validasi dan eksekusi render.
    Controller tinggal lempar data config ke sini.
    """
    
    def validate_config(self, config: dict) -> tuple[bool, str]:
        """
        Cek apakah konfigurasi valid sebelum render.
        Return: (Sukses?, PesanError)
        """
        path = config.get("output_path", "")
        
        if not path:
            return False, "Output path cannot be empty."
            
        if not path.endswith(".mp4"):
            return False, "Output must be .mp4 format."
            
        # Cek folder exist
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            return False, f"Directory not found: {directory}"
            
        return True, ""

    def start_render_process(self, project_state, config):
        """
        Memicu engine render (FFmpeg / PyAV nantinya).
        Sekarang print dulu sebagai mock.
        """
        print("\n[RENDER SERVICE] --- STARTING ---")
        print(f"Output: {config['output_path']}")
        print(f"Res: {config['resolution']}")
        print(f"FPS: {config['fps']}")
        print(f"Layers to render: {len(project_state.layers)}")
        print("[RENDER SERVICE] --- FINISHED ---")
        return True