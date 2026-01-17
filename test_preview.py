import sys
from PySide6.QtGui import QGuiApplication
from preview.text_preview import render_text_preview

class DummyStyle:
    font_path = r"C:\Windows\Fonts\arial.ttf"
    font_size = 42
    color = (255,255,255,255)
    stroke_width = 3
    stroke_color = (0,0,0,255)

app = QGuiApplication(sys.argv)

pixmap = render_text_preview(DummyStyle(), max_width=600)
print("Preview OK:", pixmap.size())
