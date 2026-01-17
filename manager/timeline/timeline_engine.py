# manager/timeline/timeline_engine.py
from typing import List, Optional
from .layer_model import LayerModel

class TimelineEngine:
    def __init__(self):
        self._layers: List[LayerModel] = []

    def add_layer(self, layer: LayerModel):
        self._layers.append(layer)
        self._sort_layers()

    def remove_layer(self, layer_id: str):
        self._layers = [l for l in self._layers if l.id != layer_id]

    def clear(self):
        self._layers.clear()

    def get_active_layers(self, t: float) -> List[LayerModel]:
        return [layer for layer in self._layers if layer.time.contains(t)]
        
    def get_layer(self, layer_id: str) -> Optional[LayerModel]:
        for layer in self._layers:
            if layer.id == layer_id:
                return layer
        return None

    # [BARU] Sumber kebenaran durasi proyek
    def get_total_duration(self) -> float:
        if not self._layers:
            return 0.0
        # Mencari waktu 'end' paling jauh dari semua layer
        return max((layer.time.end for layer in self._layers), default=0.0)

    def _sort_layers(self):
        self._layers.sort(key=lambda l: l.z_index)