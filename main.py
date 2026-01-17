# main.py
import sys
import os
from PySide6.QtWidgets import QApplication

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manager.editor_controller import EditorController
from gui.main_window import VideoEditorApp
from manager.editor_binder import EditorBinder # Import Binder Baru

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. Buat Otak (Controller)
    controller = EditorController()
    
    # 2. Buat Badan (Window)
    window = VideoEditorApp(controller)
    
    # 3. Panggil Penghulu (Binder) untuk menikahkan Otak & Badan
    binder = EditorBinder(controller, window)
    
    # Wiring Manual untuk Preview (Karena Preview ada di dalam Window)
    # Ini bagian "kabel" visual yang paling krusial
    controller.sig_layer_created.connect(window.preview_panel.on_layer_created)
    controller.sig_layer_removed.connect(window.preview_panel.on_layer_removed)
    controller.sig_property_changed.connect(window.preview_panel.on_property_changed)
    controller.sig_selection_changed.connect(window.preview_panel.on_selection_changed)
    
    window.show()
    sys.exit(app.exec())