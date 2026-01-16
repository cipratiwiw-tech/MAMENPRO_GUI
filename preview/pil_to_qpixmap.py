# preview/pil_to_qpixmap.py
from PIL.ImageQt import ImageQt
from PySide6.QtGui import QPixmap

def pil_to_qpixmap(pil_img):
    return QPixmap.fromImage(ImageQt(pil_img))
