# gui/right_panel/setting_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal

class SettingPanel(QWidget):
    sig_property_changed = Signal(dict)
    
    def __init__(self, parent=None): # <--- JANGAN ADA 'controller'
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Settings Placeholder"))
        # ... kode widget lainnya ...
        
    def set_values(self, properties):
        # Logic update UI dari data
        pass
        
    def update_form_visual(self, props):
        # Sama dengan set_values, sesuaikan nama method yg dipanggil Binder
        pass
        
    def clear_form(self):
        pass