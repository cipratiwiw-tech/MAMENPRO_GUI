# main.py
import sys
import os
from PySide6.QtWidgets import QApplication

# Tambahkan baris ini agar Python tidak bingung mencari folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import VideoEditorApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoEditorApp()
    window.show()
    sys.exit(app.exec())