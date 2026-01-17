# main.py
import sys
import os
from PySide6.QtWidgets import QApplication

# Tambahkan path root agar modul ketemu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manager.editor_controller import EditorController
from gui.main_window import VideoEditorApp
from manager.editor_binder import EditorBinder # <--- WAJIB ADA

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. Otak
    controller = EditorController()
    
    # 2. Tampilan (Tanpa Controller)
    window = VideoEditorApp()
    
    # 3. Kabel Penghubung (Binder)
    # Ini yang akan memperbaiki logika aplikasi agar tombol berfungsi
    binder = EditorBinder(controller, window)
    
    window.show()
    sys.exit(app.exec())