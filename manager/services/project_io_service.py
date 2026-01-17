# manager/services/project_io_service.py
import json
from dataclasses import asdict
from manager.project_state import ProjectState, LayerData

class ProjectIOService:
    """
    Tukang Catat. Tugasnya cuma mengubah State <-> JSON.
    Tidak peduli UI, tidak peduli Controller.
    """

    def save_project(self, state: ProjectState, file_path: str) -> bool:
        try:
            # 1. Konversi List LayerData ke List of Dict
            layers_data = [asdict(layer) for layer in state.layers]
            
            # 2. Bungkus Data Proyek
            project_data = {
                "version": "1.0",
                "layers": layers_data
            }
            
            # 3. Tulis ke File
            with open(file_path, 'w') as f:
                json.dump(project_data, f, indent=4)
            return True
            
        except Exception as e:
            print(f"[IO SERVICE ERROR] Save failed: {e}")
            return False

    def load_project(self, file_path: str) -> list[LayerData]:
        """
        Membaca file JSON dan mengembalikannya sebagai list object LayerData.
        Mengembalikan list kosong jika gagal.
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            loaded_layers = []
            if "layers" in data:
                for l_dict in data["layers"]:
                    # Konversi Dict kembali menjadi Object LayerData
                    # Kita gunakan **kwargs unpacking untuk mapping otomatis
                    layer = LayerData(**l_dict)
                    loaded_layers.append(layer)
            
            return loaded_layers
            
        except Exception as e:
            print(f"[IO SERVICE ERROR] Load failed: {e}")
            return []