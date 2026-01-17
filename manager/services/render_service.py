# manager/services/render_service.py
import os

class RenderService:
    """
    Bertanggung jawab memvalidasi request render dan 
    memicu proses rendering (FFmpeg/Engine).
    """
    
    def validate_render_config(self, config: dict) -> tuple[bool, str]:
        """
        Cek apakah config valid.
        Returns: (IsValid, ErrorMessage)
        """
        output_path = config.get("output_path", "")
        if not output_path:
            return False, "Output path is empty"
            
        # Cek apakah folder tujuan ada
        folder = os.path.dirname(output_path)
        if folder and not os.path.exists(folder):
            return False, f"Directory does not exist: {folder}"
            
        return True, ""

    def start_render(self, project_state, config: dict):
        """
        Memulai proses render.
        Di masa depan, ini akan memanggil `engine.render_engine`.
        """
        # Simulasi log
        print(f"--- RENDER SERVICE STARTED ---")
        print(f"Target: {config['output_path']}")
        print(f"Resolution: {config['resolution']}")
        print(f"FPS: {config['fps']}")
        print(f"Total Layers: {len(project_state.layers)}")
        print(f"--- RENDER SERVICE FINISHED (MOCK) ---")
        
        # Nanti return status atau object process
        return True