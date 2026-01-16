# engine/text/wrap_text.py
from typing import List
from PIL import ImageFont

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    words = text.split()
    lines, current = [], ""

    for w in words:
        trial = (current + " " + w).strip()
        if font.getlength(trial) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w

    if current:
        lines.append(current)
    return lines
