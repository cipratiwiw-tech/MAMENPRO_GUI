# engine/text/render_text.py
from typing import Tuple, List
from PIL import Image, ImageDraw, ImageFont
from .wrap_text import wrap_text
from .measure_text import measure_lines

def render_text(
    text: str,
    font_path: str,
    font_size: int,
    color: Tuple[int, int, int, int],
    max_width: int,
    line_spacing: int = 4,
    stroke_width: int = 0,
    stroke_color: Tuple[int, int, int, int] = (0, 0, 0, 255),
    padding: int = 8
) -> Image.Image:
    font = ImageFont.truetype(font_path, font_size)
    lines = wrap_text(text, font, max_width)
    w, h = measure_lines(lines, font, line_spacing)

    img = Image.new("RGBA", (w + padding*2, h + padding*2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    y = padding
    for line in lines:
        draw.text(
            (padding, y),
            line,
            fill=color,
            font=font,
            stroke_width=stroke_width,
            stroke_fill=stroke_color
        )
        y += font.getbbox("Ag")[3] + line_spacing

    return img
