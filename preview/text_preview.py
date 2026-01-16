# preview/text_preview.py
from engine.text.render_text import render_text
from engine.text.style import TextStyle
from .pil_to_qpixmap import pil_to_qpixmap

SAMPLE_TEXT = "Contoh teks"

def render_text_preview(style: TextStyle, max_width: int):
    pil_img = render_text(
        text=SAMPLE_TEXT,
        font_path=style.font_path,
        font_size=style.font_size,
        color=style.color,
        max_width=max_width,
        stroke_width=style.stroke_width,
        stroke_color=style.stroke_color,
    )
    return pil_to_qpixmap(pil_img)
