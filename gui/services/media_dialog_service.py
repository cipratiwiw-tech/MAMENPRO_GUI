# gui/services/media_dialog_service.py
import os
from PySide6.QtWidgets import QFileDialog

class MediaDialogService:
    @staticmethod
    def get_media_file(parent_widget):
        """
        Membuka dialog native OS.
        Returns: dict {'type': 'video'|'image', 'path': str} or None
        """
        path, _ = QFileDialog.getOpenFileName(
            parent_widget, 
            "Import Media", 
            "", 
            "Media Files (*.mp4 *.jpg *.png *.avi *.mov)"
        )
        
        if path:
            ext = os.path.splitext(path)[1].lower()
            ftype = "video" if ext in ['.mp4', '.avi', '.mov'] else "image"
            return {"type": ftype, "path": path}
        return None