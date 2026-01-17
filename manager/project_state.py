from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class LayerData:
    id: str
    type: str  # 'video', 'image', 'text', 'audio', 'shape', 'caption'
    name: str
    path: Optional[str] = None
    
    # Payload Properti (Flat Dictionary tapi dengan Key standar Konstitusi)
    properties: Dict = field(default_factory=lambda: {
        # --- TRANSFORM (Mandatory Visual) ---
        "x": 0, "y": 0, 
        "scale_x": 100, "scale_y": 100, # Support non-uniform scale
        "scale": 100, # Legacy support
        "rotation": 0,
        "anchor_x": 0.5, "anchor_y": 0.5, # Center default
        
        # --- APPEARANCE ---
        "opacity": 1.0,
        "blend_mode": "Normal",
        "visible": True,
        
        # --- TEXT SPECIFIC ---
        "text_content": "New Text",
        "font_family": "Arial",
        "font_size": 60,
        "text_color": "#ffffff",
        "is_bold": False,
        
        # --- TIMING (Read Only di Panel Properties, Edit di Timeline) ---
        "start_time": 0.0,
        "duration": 5.0,
        "speed": 1.0,

        # --- AUDIO ---
        "volume": 1.0,
        "mute": False,
        
        # --- CHROMA KEY ---
        "chroma_active": False,
        "chroma_color": "#00ff00",
        "chroma_threshold": 0.15
    })
    
    z_index: int = 0
    is_locked: bool = False

class ProjectState:
    def __init__(self):
        self.layers: List[LayerData] = []
        self.selected_layer_id: Optional[str] = None
        
        # GLOBAL CANVAS RESOLUTION
        self.width: int = 1080
        self.height: int = 1920

    def add_layer(self, layer: LayerData):
        self.layers.append(layer)
        self.layers.sort(key=lambda x: x.z_index)

    def get_layer(self, layer_id: str) -> Optional[LayerData]:
        return next((l for l in self.layers if l.id == layer_id), None)

    def remove_layer(self, layer_id: str):
        self.layers = [l for l in self.layers if l.id != layer_id]