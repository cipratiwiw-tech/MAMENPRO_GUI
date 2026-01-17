# gui/services/media_dialog_service.py
import os
from PySide6.QtWidgets import QFileDialog

class MediaDialogService:
    @staticmethod
    def get_media_file(parent_widget):
        """Membuka dialog import media"""
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

    @staticmethod
    def get_save_location(parent_widget, default_name="output.mp4"):
        """[BARU] Membuka dialog save file"""
        path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            "Export Video",
            default_name,
            "Video MP4 (*.mp4)"
        )
        return path
    
    @staticmethod
    def get_audio_file(parent_widget):
        """[BARU] Dialog khusus Audio"""
        path, _ = QFileDialog.getOpenFileName(
            parent_widget, 
            "Import Audio", 
            "", 
            "Audio Files (*.mp3 *.wav *.aac *.m4a)"
        )
        return path