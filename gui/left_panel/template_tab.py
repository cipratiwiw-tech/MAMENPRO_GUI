# gui/left_panel/template_tab.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import Signal, Qt

class TemplateTab(QWidget):
    # Signal: Mengirim ID template yang dipilih
    sig_apply_template = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl = QLabel("TEMPLATES")
        lbl.setStyleSheet("font-weight: bold; color: #98c379;")
        layout.addWidget(lbl)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("border: 1px solid #3e4451;")
        layout.addWidget(self.list_widget)

        # Mock Data Templates
        templates = [
            ("Intro Gaming", "tpl_gaming"),
            ("Quote of the Day", "tpl_quote"),
            ("Product Promo", "tpl_promo"),
            ("Lower Third News", "tpl_news")
        ]

        for name, code in templates:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, code)
            self.list_widget.addItem(item)

        self.list_widget.itemDoubleClicked.connect(self._on_item_dbl_clicked)

    def _on_item_dbl_clicked(self, item):
        code = item.data(Qt.UserRole)
        self.sig_apply_template.emit(code)