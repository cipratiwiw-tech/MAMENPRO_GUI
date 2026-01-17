# main.py
import sys
import os
from PySide6.QtWidgets import QApplication

# 1. Setup Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 2. Import Modules
from manager.editor_controller import EditorController
from gui.main_window import VideoEditorApp
from manager.editor_binder import EditorBinder
from gui.styles import AppTheme  # Import Theme

if __name__ == "__main__":
    # 3. Init App
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Base style Qt yang netral
    
    # 4. Apply Custom Theme
    app.setStyleSheet(AppTheme.get_stylesheet())
    
    # 5. Build Architecture
    controller = EditorController()
    window = VideoEditorApp()
    binder = EditorBinder(controller, window)
    
    # 6. Launch
    window.show()
    sys.exit(app.exec())