# manager/services/template_service.py
from manager.project_state import LayerData
import uuid

class TemplateService:
    """
    Bertanggung jawab menerjemahkan 'Template ID' menjadi 
    satu atau beberapa objek LayerData yang siap dipakai.
    """
    
    def generate_layers_from_template(self, template_id: str) -> list[LayerData]:
        """
        Returns: List of LayerData objects
        """
        layers = []
        
        if template_id == "tpl_quote":
            # Resep Quote: Background Gelap + Teks
            # 1. Background (Misal pakai Shape atau Solid Color nanti)
            # Untuk sekarang kita simulasi dengan Text Layer sebagai placeholder
            bg_id = str(uuid.uuid4())[:8]
            l1 = LayerData(
                id=bg_id, 
                type="text", 
                name="Quote BG (Placeholder)",
                properties={
                    "text_content": "⬛ [Background Area]", 
                    "font_size": 100, 
                    "opacity": 0.5
                }
            )
            
            # 2. Text Utama
            txt_id = str(uuid.uuid4())[:8]
            l2 = LayerData(
                id=txt_id, 
                type="text", 
                name="Quote Text",
                properties={
                    "text_content": "\"Insert Quote Here\"", 
                    "font_size": 80, 
                    "y": 0
                },
                z_index=1
            )
            layers.extend([l1, l2])

        elif template_id == "tpl_news":
            # Resep News: Lower Third
            lower_id = str(uuid.uuid4())[:8]
            l1 = LayerData(
                id=lower_id, 
                type="text", 
                name="Lower Third",
                properties={
                    "text_content": "BREAKING NEWS", 
                    "y": 400, 
                    "text_color": "#ff0000",
                    "is_bold": True
                }
            )
            layers.append(l1)
            
        return layers