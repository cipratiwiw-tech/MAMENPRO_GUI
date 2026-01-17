from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QFileDialog
from PySide6.QtCore import Signal

class MediaPanel(QWidget):
    sig_media_changed = Signal(str)   # 👈 TAMBAH INI

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller

        btn = QPushButton("Load Video")
        btn.clicked.connect(self._on_load_video)

        layout = QVBoxLayout(self)
        layout.addWidget(btn)

    def _on_load_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Video",
            "",
            "Video Files (*.mp4 *.mov *.avi)"
        )
        if path:
            self.controller.load_video(path)
            self.sig_media_changed.emit(path)  # 👈 TAMBAH INI
