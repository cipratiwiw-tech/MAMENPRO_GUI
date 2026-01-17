# gui/right_panel/sections/text_section.py
from PySide6.QtWidgets import (
    QWidget, QFontComboBox, QTextEdit, QPushButton, QColorDialog, 
    QHBoxLayout, QVBoxLayout, QButtonGroup, QLabel, QTabWidget, 
    QCheckBox, QComboBox, QFormLayout  # <--- SUDAH DITAMBAHKAN
)
from PySide6.QtGui import QColor, QIcon
from PySide6.QtCore import Signal, Qt
from ..base_section import BaseSection, SmartSpinBox

class ColorButton(QPushButton):
    sig_color_changed = Signal(str) 

    def __init__(self, default_color="#FFFFFF"):
        super().__init__()
        self.setFixedHeight(25)
        self.current_color = default_color
        self.clicked.connect(self._pick_color)
        self._update_style()

    def setValue(self, hex_color):
        self.current_color = hex_color
        self._update_style()

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self.current_color))
        if color.isValid():
            hex_c = color.name()
            self.setValue(hex_c)
            self.sig_color_changed.emit(hex_c)

    def _update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_color};
                border: 1px solid #5c6370;
                border-radius: 4px;
            }}
        """)

class TextSection(BaseSection):
    def __init__(self, parent=None):
        super().__init__("TEXT PROPERTIES", parent)
        
        # Gunakan Tab Widget agar rapi
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 0; }
            QTabBar::tab { background: #2c313a; color: #ccc; padding: 6px; }
            QTabBar::tab:selected { background: #3e4451; color: white; font-weight: bold; }
        """)
        
        # Inisialisasi setiap Tab
        self._init_tab_content()
        self._init_tab_style()
        self._init_tab_decor()
        self._init_tab_layout()
        
        # Masukkan Tab ke BaseSection
        self.form_layout.addRow(self.tabs)

    def _init_tab_content(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(5,5,5,5)
        
        # Content
        self.txt_content = QTextEdit()
        self.txt_content.setFixedHeight(80)
        self.txt_content.setStyleSheet("background: #21252b; color: #eee; border: 1px solid #3e4451;")
        self.txt_content.textChanged.connect(lambda: self.sig_edit_changed.emit("text.content", self.txt_content.toPlainText()))
        layout.addWidget(QLabel("Content:"))
        layout.addWidget(self.txt_content)
        
        # Auto Wrap
        self.chk_wrap = QCheckBox("Auto Wrap Text")
        self.chk_wrap.setStyleSheet("color: #ccc;")
        self.chk_wrap.stateChanged.connect(lambda v: self.sig_edit_changed.emit("text.wrap", v == 2))
        layout.addWidget(self.chk_wrap)
        
        layout.addStretch()
        self.tabs.addTab(w, "📝")

    def _init_tab_style(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setContentsMargins(5,15,5,5)

        # Font Family
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(lambda f: self.sig_edit_changed.emit("text.font_family", f.family()))
        layout.addRow("Family:", self.font_combo)

        # Size
        self.spin_size = self._create_spin(1, 500, suffix=" pt")
        self._prop_map["text.font_size"] = {"widget": self.spin_size, "in": lambda x: x, "out": lambda x: x}
        self._connect_lifecycle(self.spin_size, "text.font_size")
        layout.addRow("Size:", self.spin_size)

        # Weight (100-900)
        self.combo_weight = QComboBox()
        weights = ["Thin", "Light", "Normal", "Medium", "Bold", "Black"]
        self.combo_weight.addItems(weights)
        self.combo_weight.currentTextChanged.connect(lambda t: self.sig_edit_changed.emit("text.weight", t))
        layout.addRow("Weight:", self.combo_weight)

        # Italic
        self.chk_italic = QCheckBox("Italic")
        self.chk_italic.setStyleSheet("color: #ccc;")
        self.chk_italic.stateChanged.connect(lambda v: self.sig_edit_changed.emit("text.italic", v == 2))
        layout.addRow("", self.chk_italic)

        self.tabs.addTab(w, "Aa")

    def _init_tab_decor(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setContentsMargins(5,15,5,5)

        # --- FILL ---
        self.btn_color = ColorButton("#FFFFFF")
        self.btn_color.sig_color_changed.connect(lambda c: self.sig_edit_changed.emit("text.color", c))
        layout.addRow("Fill Color:", self.btn_color)

        # --- STROKE ---
        self.chk_stroke = QCheckBox("Enable Stroke")
        self.chk_stroke.setStyleSheet("color: #56b6c2; font-weight: bold;")
        self.chk_stroke.stateChanged.connect(lambda v: self.sig_edit_changed.emit("text.stroke_enabled", v == 2))
        layout.addRow(self.chk_stroke)

        self.btn_stroke_color = ColorButton("#000000")
        self.btn_stroke_color.sig_color_changed.connect(lambda c: self.sig_edit_changed.emit("text.stroke_color", c))
        layout.addRow("  Color:", self.btn_stroke_color)

        self.spin_stroke_width = self._create_spin(0, 50, suffix=" px")
        self._prop_map["text.stroke_width"] = {"widget": self.spin_stroke_width, "in": lambda x: x, "out": lambda x: x}
        self._connect_lifecycle(self.spin_stroke_width, "text.stroke_width")
        layout.addRow("  Width:", self.spin_stroke_width)

        # --- SHADOW ---
        self.chk_shadow = QCheckBox("Enable Shadow")
        self.chk_shadow.setStyleSheet("color: #56b6c2; font-weight: bold; margin-top: 10px;")
        self.chk_shadow.stateChanged.connect(lambda v: self.sig_edit_changed.emit("text.shadow_enabled", v == 2))
        layout.addRow(self.chk_shadow)

        self.btn_shadow_color = ColorButton("#000000")
        self.btn_shadow_color.sig_color_changed.connect(lambda c: self.sig_edit_changed.emit("text.shadow_color", c))
        layout.addRow("  Color:", self.btn_shadow_color)
        
        self.spin_shadow_blur = self._create_spin(0, 50, suffix=" px")
        self._prop_map["text.shadow_blur"] = {"widget": self.spin_shadow_blur, "in": lambda x: x, "out": lambda x: x}
        self._connect_lifecycle(self.spin_shadow_blur, "text.shadow_blur")
        layout.addRow("  Blur:", self.spin_shadow_blur)
        
        # Offset X/Y
        hb = QHBoxLayout()
        self.spin_shadow_x = self._create_spin(-50, 50, suffix=" x")
        self.spin_shadow_y = self._create_spin(-50, 50, suffix=" y")
        
        self._prop_map["text.shadow_x"] = {"widget": self.spin_shadow_x, "in": lambda x: x, "out": lambda x: x}
        self._connect_lifecycle(self.spin_shadow_x, "text.shadow_x")
        self._prop_map["text.shadow_y"] = {"widget": self.spin_shadow_y, "in": lambda x: x, "out": lambda x: x}
        self._connect_lifecycle(self.spin_shadow_y, "text.shadow_y")
        
        hb.addWidget(self.spin_shadow_x)
        hb.addWidget(self.spin_shadow_y)
        layout.addRow("  Offset:", hb)

        self.tabs.addTab(w, "🎨")

    def _init_tab_layout(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setContentsMargins(5,15,5,5)

        # Alignment
        self.btn_left = QPushButton("L"); self.btn_left.setCheckable(True)
        self.btn_center = QPushButton("C"); self.btn_center.setCheckable(True)
        self.btn_right = QPushButton("R"); self.btn_right.setCheckable(True)
        
        self.group_align = QButtonGroup(self)
        self.group_align.addButton(self.btn_left, 1)
        self.group_align.addButton(self.btn_center, 2)
        self.group_align.addButton(self.btn_right, 3)
        self.group_align.idClicked.connect(self._on_align_clicked)
        
        h_align = QHBoxLayout()
        for b in [self.btn_left, self.btn_center, self.btn_right]:
            b.setFixedWidth(30)
            h_align.addWidget(b)
        layout.addRow("Align:", h_align)

        # Spacing
        self.spin_line_height = self._create_spin(0.5, 5.0, step=0.1)
        self._prop_map["text.line_height"] = {"widget": self.spin_line_height, "in": lambda x: x, "out": lambda x: x}
        self._connect_lifecycle(self.spin_line_height, "text.line_height")
        layout.addRow("Line Height:", self.spin_line_height)

        self.spin_letter_spacing = self._create_spin(-20, 100, step=1, suffix=" px")
        self._prop_map["text.letter_spacing"] = {"widget": self.spin_letter_spacing, "in": lambda x: x, "out": lambda x: x}
        self._connect_lifecycle(self.spin_letter_spacing, "text.letter_spacing")
        layout.addRow("Letter Space:", self.spin_letter_spacing)

        self.tabs.addTab(w, "📐")

    def _create_spin(self, min_val, max_val, step=1.0, suffix=""):
        sb = SmartSpinBox()
        sb.setRange(min_val, max_val)
        sb.setSingleStep(step)
        sb.setSuffix(suffix)
        sb.setStyleSheet("background-color: #21252b; color: #dcdcdc; border: 1px solid #3e4451;")
        return sb

    def _on_align_clicked(self, btn_id):
        m = {1: 'left', 2: 'center', 3: 'right'}
        self.sig_edit_changed.emit("text.align", m.get(btn_id, 'left'))

    def apply_state(self, props: dict):
        t = props.get("text", {})
        
        # 1. Content
        self.txt_content.blockSignals(True)
        self.txt_content.setPlainText(t.get("content", ""))
        self.txt_content.blockSignals(False)
        
        self.chk_wrap.blockSignals(True)
        self.chk_wrap.setChecked(t.get("wrap", False))
        self.chk_wrap.blockSignals(False)

        # 2. Style
        self.font_combo.blockSignals(True)
        self.font_combo.setCurrentFont(t.get("font_family", "Arial"))
        self.font_combo.blockSignals(False)
        
        self._set_widget_value("text.font_size", t.get("font_size", 60))
        self.combo_weight.setCurrentText(t.get("weight", "Normal"))
        self.chk_italic.setChecked(t.get("italic", False))

        # 3. Decor
        self.btn_color.setValue(t.get("color", "#FFFFFF"))
        
        # Stroke
        self.chk_stroke.setChecked(t.get("stroke_enabled", False))
        self.btn_stroke_color.setValue(t.get("stroke_color", "#000000"))
        self._set_widget_value("text.stroke_width", t.get("stroke_width", 2))
        
        # Shadow
        self.chk_shadow.setChecked(t.get("shadow_enabled", False))
        self.btn_shadow_color.setValue(t.get("shadow_color", "#000000"))
        self._set_widget_value("text.shadow_blur", t.get("shadow_blur", 5))
        self._set_widget_value("text.shadow_x", t.get("shadow_x", 5))
        self._set_widget_value("text.shadow_y", t.get("shadow_y", 5))

        # 4. Layout
        a = t.get("align", "left")
        if a == "center": self.btn_center.setChecked(True)
        elif a == "right": self.btn_right.setChecked(True)
        else: self.btn_left.setChecked(True)
        
        self._set_widget_value("text.line_height", t.get("line_height", 1.2))
        self._set_widget_value("text.letter_spacing", t.get("letter_spacing", 0))