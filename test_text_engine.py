# test_text_engine.py
from engine.text.render_text import render_text

FONT_PATH = r"C:\Windows\Fonts\arial.ttf"

img = render_text(
    text="Ini contoh caption yang panjang untuk diuji wrapping",
    font_path=FONT_PATH,
    font_size=42,
    color=(255, 255, 255, 255),
    max_width=600,
    stroke_width=3
)

img.save("out.png")
print("OK: out.png generated")
