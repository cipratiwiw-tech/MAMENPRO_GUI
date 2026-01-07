import os
from PySide6.QtWidgets import QFileDialog

class MediaManager:
    @staticmethod
    def open_media_dialog(parent, title="Pilih Media"):
        """Mengambil Video atau Gambar"""
        filters = "All Media (*.mp4 *.mov *.png *.jpg *.jpeg);;Videos (*.mp4 *.mov);;Images (*.png *.jpg)"
        file_path, _ = QFileDialog.getOpenFileName(parent, title, "", filters)
        if file_path:
            return {
                "path": file_path,
                "name": os.path.basename(file_path),
                "type": "image" if file_path.lower().endswith(('.png', '.jpg', '.jpeg')) else "video"
            }
        return None

    @staticmethod
    def open_audio_dialog(parent):
        """Mengambil File Musik"""
        file_path, _ = QFileDialog.getOpenFileName(parent, "Pilih Musik", "", "Audio (*.mp3 *.wav *.m4a)")
        if file_path:
            return {"path": file_path, "name": os.path.basename(file_path)}
        return None