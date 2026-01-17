
# gui/left_panel/utilities_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from gui.panels.caption_panel import CaptionPanel
from gui.right_panel.bulk_tab import BulkTab 

class UtilitiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab { width: 100px; padding: 5px; }
        """)
        
        # 1. AI Caption (Reuse Panel)
        self.caption_panel = CaptionPanel()
        self.tabs.addTab(self.caption_panel, "AI Caption")
        
        # 2. Bulk Create (Reuse Tab)
        self.bulk_panel = BulkTab()
        self.tabs.addTab(self.bulk_panel, "Bulk Gen")
        
        self.layout.addWidget(self.tabs)
