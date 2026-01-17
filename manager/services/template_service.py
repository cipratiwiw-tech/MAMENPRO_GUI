# manager/services/template_service.py
from manager.project_state import LayerData
import uuid

class TemplateService:
    """
    Service khusus untuk meracik layer-layer berdasarkan resep template.
    MURNI LOGIC & DATA. Tidak ada UI.
    """
    
    def generate_layers(self, template_id: str) -> list[LayerData]:
        """
        Menerima ID, Mengembalikan List LayerData baru.
        """
        layers = []
        
        if template_id == "tpl_quote":
            # Resep 1: Background Gelap
            bg = LayerData(
                id=str(uuid.uuid4())[:8],
                type="text", # Sementara pakai text sbg placeholder shape
                name="Background",
                properties={
                    "text_content": "⬛ [BG AREA]", 
                    "font_size": 150, 
                    "opacity": 0.3,
                    "text_color": "#000000"
                },
                z_index=0
            )
            
            # Resep 2: Teks Quote
            txt = LayerData(
                id=str(uuid.uuid4())[:8],
                type="text",
                name="Quote Text",
                properties={
                    "text_content": "\"Insert Your Quote Here\"", 
                    "font_size": 60,
                    "y": 0,
                    "is_bold": True
                },
                z_index=1
            )
            layers.extend([bg, txt])

        elif template_id == "tpl_news":
            # Resep News Lower Third
            l3 = LayerData(
                id=str(uuid.uuid4())[:8],
                type="text",
                name="News Ticker",
                properties={
                    "text_content": "🔴 BREAKING NEWS: LIVE REPORT",
                    "y": 400,
                    "font_size": 40,
                    "text_color": "#ff0000",
                    "is_bold": True
                }
            )
            layers.append(l3)
            
        return layers