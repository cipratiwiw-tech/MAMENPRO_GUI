# main.py
import sys
import os
from PySide6.QtWidgets import QApplication

# Pastikan root folder terdeteksi
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manager.editor_controller import EditorController
from gui.main_window import VideoEditorApp
from manager.editor_binder import EditorBinder

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. MODEL & CONTROLLER (Logic)
    controller = EditorController()
    
    # 2. VIEW (UI)
    # MainWindow sekarang bersih, tidak terima controller
    window = VideoEditorApp()
    
    # 3. BINDER (Wiring)
    # Menikahkan Logic dan UI
    binder = EditorBinder(controller, window)
    
    # 4. START
    window.show()
    sys.exit(app.exec())