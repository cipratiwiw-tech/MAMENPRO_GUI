from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QSizePolicy
from PySide6.QtGui import QPen, QColor, QBrush

class PreviewPanel(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ⚠️ KUNCI ANTI STYLESHEET
        self.setStyleSheet("background: transparent;")
        self.viewport().setStyleSheet("background: transparent;")

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.scene.addRect(
            0, 0, 500, 300,
            QPen(QColor("yellow"), 5),
            QBrush(QColor("#4444ff"))
        )

        self.setSceneRect(0, 0, 500, 300)
