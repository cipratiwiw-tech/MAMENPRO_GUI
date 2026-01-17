# manager/services/render_service.py
import os
import threading
from engine.render_engine import RenderEngine # [BARU] Import Engine

class RenderService:
    """
    Service validasi dan eksekusi render.
    Sekarang sudah terhubung ke RenderEngine asli.
    """
    
    def __init__(self):
        self.engine = RenderEngine()

    def validate_config(self, config: dict) -> tuple[bool, str]:
        path = config.get("output_path", "")
        if not path:
            return False, "Output path cannot be empty."
        if not path.endswith(".mp4"):
            return False, "Output must be .mp4 format."
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            return False, f"Directory not found: {directory}"
        return True, ""

    def start_render_process(self, project_state, config):
        """
        Menjalankan render di Thread terpisah agar UI tidak macet (Not Responding).
        """
        # Kita gunakan Threading agar GUI tetap responsif saat render berjalan
        render_thread = threading.Thread(
            target=self._run_engine_safe,
            args=(project_state, config)
        )
        render_thread.start()
        return True

    def _run_engine_safe(self, state, config):
        # Wrapper untuk menjalankan engine
        try:
            success = self.engine.render_project(
                state, 
                config['output_path'], 
                config
            )
            if success:
                print("[SERVICE] Render finished successfully.")
            else:
                print("[SERVICE] Render returned failure.")
        except Exception as e:
            print(f"[SERVICE] Render Exception: {e}")