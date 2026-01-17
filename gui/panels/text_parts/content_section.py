# gui/panels/text_parts/content_section.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PySide6.QtCore import Signal

class ContentSection(QWidget):
    sig_content_changed = Signal(dict) # {text_content}

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        layout.addWidget(QLabel("Content:"))
        self.txt_edit = QTextEdit()
        self.txt_edit.setMaximumHeight(100)
        self.txt_edit.textChanged.connect(self._emit_change)
        layout.addWidget(self.txt_edit)

    def _emit_change(self):
        self.sig_content_changed.emit({
            "text_content": self.txt_edit.toPlainText()
        })

    def set_values(self, props):
        if "text_content" in props:
            self.txt_edit.blockSignals(True)
            self.txt_edit.setPlainText(props["text_content"])
            self.txt_edit.blockSignals(False)