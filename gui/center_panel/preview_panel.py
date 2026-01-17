# gui/center_panel/preview_panel.py

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene

class PreviewPanel(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.video_item = None

    def set_video_item(self, video_item):
        self.scene.clear()
        self.video_item = video_item
        self.scene.addItem(video_item)
