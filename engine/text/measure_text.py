# engine/text/measure_text.py
from typing import List, Tuple
from PIL import ImageFont

def measure_lines(
    lines: List[str],
    font: ImageFont.FreeTypeFont,
    line_spacing: int = 4
) -> Tuple[int, int]:
    widths = [int(font.getlength(l)) for l in lines] if lines else [0]
    line_height = font.getbbox("Ag")[3]
    height = len(lines) * line_height + max(0, len(lines) - 1) * line_spacing
    return max(widths), height
