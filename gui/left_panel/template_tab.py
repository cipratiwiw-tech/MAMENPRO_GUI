# gui/left_panel/template_tab.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import Signal, Qt

class TemplateTab(QWidget):
    # SIGNAL OUT: User memilih template ID ini
    sig_apply_template = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl = QLabel("PRESET TEMPLATES")
        lbl.setStyleSheet("font-weight: bold; color: #98c379; margin-bottom: 5px;")
        layout.addWidget(lbl)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("border: 1px solid #3e4451;")
        layout.addWidget(self.list_widget)

        # Static Data (Hanya UI)
        templates = [
            ("📝 Quote Generator", "tpl_quote"),
            ("📰 News Lower Third", "tpl_news"),
            ("🎬 Simple Intro", "tpl_intro")
        ]

        for name, code in templates:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, code)
            self.list_widget.addItem(item)

        # Event
        self.list_widget.itemDoubleClicked.connect(self._on_dbl_click)
        
        lbl_hint = QLabel("Double click to apply")
        lbl_hint.setStyleSheet("color: #5c6370; font-size: 10px; font-style: italic;")
        layout.addWidget(lbl_hint)

    def _on_dbl_click(self, item):
        tpl_id = item.data(Qt.UserRole)
        # EMIT SIGNAL (Jangan panggil controller!)
        self.sig_apply_template.emit(tpl_id)