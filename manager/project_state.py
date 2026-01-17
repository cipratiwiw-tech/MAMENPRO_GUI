# manager/project_state.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class LayerData:
    id: str
    type: str  # 'video', 'image', 'text'
    name: str
    path: Optional[str] = None
    
    properties: Dict = field(default_factory=lambda: {
        "x": 0, "y": 0, "scale": 100, "opacity": 1.0, "rotation": 0,
        "start_time": 0.0, "duration": 5.0,
        "text_content": "Double Click to Edit",
        "font_family": "Arial",
        "font_size": 60,
        "text_color": "#ffffff",
        "is_bold": False
    })
    
    z_index: int = 0
    is_locked: bool = False

class ProjectState:
    def __init__(self):
        self.layers: List[LayerData] = []
        self.selected_layer_id: Optional[str] = None
        
        # [NEW] GLOBAL CANVAS RESOLUTION
        # Default 1080x1920 (9:16) agar sesuai default Preview
        self.width: int = 1080
        self.height: int = 1920

    def add_layer(self, layer: LayerData):
        self.layers.append(layer)
        self.layers.sort(key=lambda x: x.z_index)

    def get_layer(self, layer_id: str) -> Optional[LayerData]:
        return next((l for l in self.layers if l.id == layer_id), None)

    def remove_layer(self, layer_id: str):
        self.layers = [l for l in self.layers if l.id != layer_id]