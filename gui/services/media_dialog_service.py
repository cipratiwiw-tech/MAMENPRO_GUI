# gui/services/media_dialog_service.py
import os
from PySide6.QtWidgets import QFileDialog

class MediaDialogService:
    @staticmethod
    def open_import_dialog(parent):
        """
        Membuka dialog untuk memilih file media (Video/Image).
        Returns: dict {'path': str, 'type': str} atau None
        """
        filters = "Media Files (*.mp4 *.mov *.avi *.png *.jpg *.jpeg *.webp);;Video (*.mp4 *.mov *.avi);;Image (*.png *.jpg *.jpeg *.webp)"
        file_path, _ = QFileDialog.getOpenFileName(parent, "Import Media", "", filters)
        
        if file_path:
            # Deteksi tipe sederhana berdasarkan ekstensi
            ext = os.path.splitext(file_path)[1].lower()
            media_type = "video" if ext in ['.mp4', '.mov', '.avi'] else "image"
            
            return {
                "path": file_path,
                "type": media_type,
                "name": os.path.basename(file_path)
            }
        return None