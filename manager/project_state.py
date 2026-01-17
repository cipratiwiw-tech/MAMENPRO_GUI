# manager/project_state.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import uuid

@dataclass
class LayerData:
    id: str
    type: str  # 'video', 'image', 'text', 'shape'
    name: str
    path: Optional[str] = None
    # Menyimpan state visual (x, y, scale, text content, dll)
    properties: Dict = field(default_factory=lambda: {
        "x": 0, "y": 0, "scale": 100, "opacity": 1.0, 
        "rotation": 0, "text_content": "New Text", 
        "start_time": 0.0, "duration": 5.0
    })
    z_index: int = 0
    is_locked: bool = False

class ProjectState:
    def __init__(self):
        self.layers: List[LayerData] = []
        self.selected_layer_id: Optional[str] = None

    def add_layer(self, layer: LayerData):
        self.layers.append(layer)
        # Sort layer berdasarkan z_index (penting untuk rendering urutan tumpukan)
        self.layers.sort(key=lambda x: x.z_index)

    def get_layer(self, layer_id: str) -> Optional[LayerData]:
        # Cari layer berdasarkan ID
        return next((l for l in self.layers if l.id == layer_id), None)

    def remove_layer(self, layer_id: str):
        self.layers = [l for l in self.layers if l.id != layer_id]