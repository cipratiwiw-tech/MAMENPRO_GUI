# gui/right_panel/base_section.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QDoubleSpinBox, QSlider, QComboBox
from PySide6.QtCore import Signal, Qt

class SmartSpinBox(QDoubleSpinBox):
    """Wrapper QDoubleSpinBox untuk menangkap Lifecycle Edit."""
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

    def add_row(self, label_text, layout_widget, property_path, control_widget=None, converter_in=None, converter_out=None):
        """
        layout_widget: Widget yang ditampilkan di UI (bisa Container).
        control_widget: Widget logic (Slider/SpinBox). Jika None, pakai layout_widget.
        """
        # Tentukan widget mana yang punya Logic/Value
        target_widget = control_widget if control_widget else layout_widget
        
        # Tambahkan widget TAMPILAN ke layout
        self.form_layout.addRow(label_text, layout_widget)
        
        # Register widget LOGIKA ke map
        self._prop_map[property_path] = {
            "widget": target_widget,
            "in": converter_in if converter_in else lambda x: x,
            "out": converter_out if converter_out else lambda x: x
        }
        
        # Sambungkan sinyal dari widget LOGIKA
        self._connect_lifecycle(target_widget, property_path)

    def _connect_lifecycle(self, widget, path):
        # --- SPINBOX ---
        if isinstance(widget, (SmartSpinBox, QDoubleSpinBox)):
            if hasattr(widget, 'sig_edit_start'):
                widget.sig_edit_start.connect(lambda: self.sig_edit_started.emit(path))
            widget.valueChanged.connect(lambda v: self._on_widget_value_changed(path, v))
            if hasattr(widget, 'sig_edit_end'):
                widget.sig_edit_end.connect(lambda: self.sig_edit_finished.emit(path))
            else:
                widget.editingFinished.connect(lambda: self.sig_edit_finished.emit(path))

        # --- SLIDER ---
        elif isinstance(widget, QSlider):
            widget.sliderPressed.connect(lambda: self.sig_edit_started.emit(path))
            widget.valueChanged.connect(lambda v: self._on_widget_value_changed(path, v))
            widget.sliderReleased.connect(lambda: self.sig_edit_finished.emit(path))

        # --- COMBOBOX ---
        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(lambda v: self._on_combo_changed(path, v))

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