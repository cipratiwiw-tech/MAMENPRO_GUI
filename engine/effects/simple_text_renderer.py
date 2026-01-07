import numpy as np
from PIL import Image, ImageDraw, ImageFont

class SimpleTextRenderer:
    @staticmethod
    def render(settings):
        """
        Menerima dictionary settings, mengembalikan Numpy Array (H, W, 4) RGBA.
        Pure Python logic, independen dari GUI Qt.
        """
        # 1. Konfigurasi Canvas (Resolusi Tinggi untuk Preview Tajam)
        width, height = 1080, 1080 
        # Mode RGBA (Transparent Background)
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 2. Ambil Data dari Settings
        text = settings.get("text_content", "Sample Text")
        font_family = settings.get("font_family", "Arial")
        font_size = int(settings.get("font_size", 80))
        color_hex = settings.get("text_color", "#ffffff")
        align = settings.get("text_align", "center") # left, center, right
        is_paragraph = settings.get("is_paragraph", False)
        
        # 3. Load Font (Fallback mechanism)
        font = None
        try:
            # Coba load font sistem (Windows/Linux path berbeda, ini basic attempt)
            # Idealnya menggunakan library font manager, tapi ini cukup untuk basic
            font = ImageFont.truetype(f"{font_family}.ttf", font_size)
        except OSError:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()

        # 4. Parsing Warna (#RRGGBB -> RGB)
        color_hex = color_hex.lstrip('#')
        if len(color_hex) == 6:
            rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4)) + (255,) # + Alpha 255
        else:
            rgb = (255, 255, 255, 255)

        # 5. Logika Posisi (Layouting)
        # PIL Anchor: 'mm' = middle-middle, 'lm' = left-middle, etc.
        xy = (width/2, height/2)
        anchor = "mm"
        align_pil = "center" # Parameter align untuk multiline text di PIL
        
        if is_paragraph:
            # Mode Paragraf (Multiline support dari PIL)
            if align == "left":
                xy = (50, height/2) # Padding kiri
                anchor = "lm"
                align_pil = "left"
            elif align == "right":
                xy = (width-50, height/2)
                anchor = "rm"
                align_pil = "right"
            else:
                align_pil = "center"
        else:
            # Mode Judul Singkat
            if align == "left": 
                anchor = "lm"
                xy = (width/2 - 200, height/2) # Offset visual
            elif align == "right":
                anchor = "rm"
                xy = (width/2 + 200, height/2)
            
        # 6. Gambar Teks ke Image
        draw.text(
            xy, 
            text, 
            font=font, 
            fill=rgb, 
            anchor=anchor, 
            align=align_pil
        )
        
        # 7. Konversi ke Numpy Array
        # Return array uint8 (Height, Width, Channels)
        return np.array(img)