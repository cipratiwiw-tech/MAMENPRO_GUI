# engine/text/style.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class TextStyle:
    font_path: str
    font_size: int
    color: Tuple[int, int, int, int]
    stroke_width: int = 0
    stroke_color: Tuple[int, int, int, int] = (0, 0, 0, 255)
