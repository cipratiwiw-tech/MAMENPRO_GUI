# gui/right_panel/base_section.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QDoubleSpinBox, 
    QSlider, QComboBox, QPushButton, QHBoxLayout, QLabel
)
from PySide6.QtCore import Signal, Qt

class KeyframeButton(QPushButton):
    """Tombol Diamond (♦) untuk Toggle Animasi"""
    sig_toggled = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setFixedSize(20, 20)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self.toggled.connect(self._on_toggle)

    def _on_toggle(self, checked):
        self._update_style()
        self.sig_toggled.emit(checked)

    def _update_style(self):
        if self.isChecked():
            # AKTIF: Diamond Merah/Orange Solid
            self.setText("♦") 
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #e06c75; 
                    border: none;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
        else:
            # NON-AKTIF: Diamond Outline Abu
            self.setText("◇")
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #5c6370; 
                    border: none;
                    font-size: 16px;
                }
                QPushButton:hover { color: #dcdcdc; }
            """)

class SmartSpinBox(QDoubleSpinBox):
    sig_edit_start = Signal()
    sig_edit_end = Signal()

    def focusInEvent(self, event):
        self.sig_edit_start.emit()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.sig_edit_end.emit()
        super().focusOutEvent(event)

class BaseSection(QWidget):
    # 3-Phase Signal System
    sig_edit_started = Signal(str)
    sig_edit_changed = Signal(str, object)
    sig_edit_finished = Signal(str)
    
    # NEW: Signal Keyframe
    sig_keyframe_toggled = Signal(str, bool) # path, is_active

    def __init__(self, title="Section", parent=None):
        super().__init__(parent)
        self._is_updating_from_code = False
        self._prop_map = {}

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 5, 0, 5)
        self.main_layout.setSpacing(0)

        self.group = QGroupBox(title)
        self.group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #3e4451; 
                border-radius: 4px; 
                margin-top: 10px; 
                padding-top: 15px;
                color: #56b6c2; 
                background-color: #282c34;
            }
        """)
        self.form_layout = QFormLayout(self.group)
        self.form_layout.setSpacing(8)
        self.form_layout.setContentsMargins(10, 10, 10, 10)
        
        self.main_layout.addWidget(self.group)

    def add_row(self, label_text, layout_widget, property_path, control_widget=None, converter_in=None, converter_out=None, enable_keyframe=True):
        """
        enable_keyframe: Jika True, tambahkan tombol diamond di sebelah label.
        """
        target_widget = control_widget if control_widget else layout_widget
        
        # --- 1. KEYFRAME BUTTON INJECTION ---
        if enable_keyframe:
            # Buat Container [Diamond] [Label]
            label_container = QWidget()
            h_label = QHBoxLayout(label_container)
            h_label.setContentsMargins(0,0,0,0)
            h_label.setSpacing(5)
            
            btn_kf = KeyframeButton()
            btn_kf.sig_toggled.connect(lambda active: self.sig_keyframe_toggled.emit(property_path, active))
            
            lbl = QLabel(label_text)
            
            h_label.addWidget(btn_kf)
            h_label.addWidget(lbl)
            
            # Tambahkan ke Form Layout sebagai LABEL (Kolom Kiri)
            self.form_layout.addRow(label_container, layout_widget)
            
            # Simpan referensi tombol keyframe (optional, untuk update state dari backend nanti)
            # self._kf_map[property_path] = btn_kf 
        else:
            # Tampilan biasa tanpa keyframe
            self.form_layout.addRow(label_text, layout_widget)
        
        # --- 2. REGISTER LOGIC ---
        self._prop_map[property_path] = {
            "widget": target_widget,
            "in": converter_in if converter_in else lambda x: x,
            "out": converter_out if converter_out else lambda x: x
        }
        
        self._connect_lifecycle(target_widget, property_path)

    def _connect_lifecycle(self, widget, path):
        # ... (Sama seperti sebelumnya) ...
        # Copy-paste method _connect_lifecycle dari versi sebelumnya di sini
        if isinstance(widget, (SmartSpinBox, QDoubleSpinBox)):
            if hasattr(widget, 'sig_edit_start'):
                widget.sig_edit_start.connect(lambda: self.sig_edit_started.emit(path))
            widget.valueChanged.connect(lambda v: self._on_widget_value_changed(path, v))
            if hasattr(widget, 'sig_edit_end'):
                widget.sig_edit_end.connect(lambda: self.sig_edit_finished.emit(path))
            else:
                widget.editingFinished.connect(lambda: self.sig_edit_finished.emit(path))

        elif isinstance(widget, QSlider):
            widget.sliderPressed.connect(lambda: self.sig_edit_started.emit(path))
            widget.valueChanged.connect(lambda v: self._on_widget_value_changed(path, v))
            widget.sliderReleased.connect(lambda: self.sig_edit_finished.emit(path))

        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(lambda v: self._on_combo_changed(path, v))
            
        elif hasattr(widget, 'textChanged'): # Untuk QTextEdit
             pass # Sudah dihandle manual di TextSection

    def _on_widget_value_changed(self, path, ui_value):
        if self._is_updating_from_code: return
        converter = self._prop_map[path]["out"]
        model_value = converter(ui_value)
        self.sig_edit_changed.emit(path, model_value)

    def _on_combo_changed(self, path, value):
        if self._is_updating_from_code: return
        self.sig_edit_started.emit(path)
        self.sig_edit_changed.emit(path, value)
        self.sig_edit_finished.emit(path)

    def _set_widget_value(self, path, model_value):
        if path not in self._prop_map: return
        meta = self._prop_map[path]
        widget = meta["widget"]
        converter_in = meta["in"]
        
        ui_value = converter_in(model_value)
        
        self._is_updating_from_code = True
        try:
            if isinstance(widget, (QDoubleSpinBox, QSlider)):
                widget.setValue(ui_value)
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(str(ui_value))
        finally:
            self._is_updating_from_code = False