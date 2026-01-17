from typing import List, Optional
from .layer_model import LayerModel

class TimelineEngine:
    def __init__(self):
        # Database internal layer
        self._layers: List[LayerModel] = []

    def add_layer(self, layer: LayerModel):
        """Menambahkan layer ke dalam timeline."""
        self._layers.append(layer)
        # Sort layer berdasarkan Z-Index (rendah ke tinggi) agar urutan render benar
        self._sort_layers()

    def remove_layer(self, layer_id: str):
        """Menghapus layer berdasarkan ID."""
        self._layers = [l for l in self._layers if l.id != layer_id]

    def clear(self):
        self._layers.clear()

    def get_layer(self, layer_id: str) -> Optional[LayerModel]:
        for layer in self._layers:
            if layer.id == layer_id:
                return layer
        return None

    def get_active_layers(self, t: float) -> List[LayerModel]:
        """
        Query Utama: Mengembalikan semua layer yang aktif pada waktu t.
        Diurutkan berdasarkan Z-Index.
        """
        return [layer for layer in self._layers if layer.time.contains(t)]

    def _sort_layers(self):
        self._layers.sort(key=lambda l: l.z_index)