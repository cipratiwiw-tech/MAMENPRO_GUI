# manager/editor_controller.py
from PySide6.QtGui import QPixmap
from canvas.video_item import VideoItem

class EditorController:
    def __init__(self, preview_panel):
        self.preview_panel = preview_panel
        self.video_item = None

    def load_video(self, video_path: str):
        self.video_item = VideoItem()

        # placeholder visual biar KELIHATAN
        pixmap = QPixmap(640, 360)
        pixmap.fill(Qt.darkGray)

        self.video_item.set_pixmap(pixmap)
        self.preview_panel.set_video_item(self.video_item)

    def update_text_preview(self):
        # sementara belum dipakai
        pass
    def on_text_changed(self, data: dict):
        # stub dulu, nanti diisi preview teks
        pass
