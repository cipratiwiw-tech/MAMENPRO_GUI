# canvas/text_item.py
from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem, QStyle, QGraphicsDropShadowEffect
from PySide6.QtGui import QFont, QColor, QPen, QTextOption, QTextBlockFormat, QTextCursor, QTextCharFormat
from PySide6.QtCore import Qt, Signal

class TextItem(QGraphicsTextItem): 
    sig_transform_changed = Signal(str, dict)

    def __init__(self, layer_id, text="New Text"):
        super().__init__(text)
        self.layer_id = layer_id
        
        self.start_time = 0.0
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        # Default Style
        self._font_family = "Arial"
        self._font_size = 60
        self._color = "#ffffff"
        self._weight = "Normal"
        self._italic = False
        self._wrap = False
        
        # Typography
        self._align = "left"
        self._line_height = 1.2
        self._letter_spacing = 0
        
        # Decor
        self._stroke_enabled = False
        self._stroke_color = "#000000"
        self._stroke_width = 2
        
        self._shadow_enabled = False
        self._shadow_color = "#000000"
        self._shadow_blur = 5
        self._shadow_x = 5
        self._shadow_y = 5
        
        self._apply_style()
        self.setZValue(0)

    def _apply_style(self):
        # 1. Font Construction
        font = QFont(self._font_family, self._font_size)
        
        # Map Weight String -> QFont.Weight
        w_map = {
            "Thin": QFont.Thin, "Light": QFont.Light, 
            "Normal": QFont.Normal, "Medium": QFont.Medium,
            "Bold": QFont.Bold, "Black": QFont.Black
        }
        font.setWeight(w_map.get(self._weight, QFont.Normal))
        font.setItalic(self._italic)
        
        if self._letter_spacing != 0:
            font.setLetterSpacing(QFont.AbsoluteSpacing, self._letter_spacing)
            
        self.setFont(font)

        # 2. Color & Stroke (Using CharFormat)
        fmt = QTextCharFormat()
        fmt.setFont(font)
        
        # Fill Color
        fmt.setForeground(QColor(self._color))
        
        # Stroke (Outline)
        if self._stroke_enabled and self._stroke_width > 0:
            pen = QPen(QColor(self._stroke_color))
            pen.setWidth(self._stroke_width)
            fmt.setTextOutline(pen)
        else:
            fmt.setTextOutline(QPen(Qt.NoPen))
            
        # Apply Format to All Text
        cursor = QTextCursor(self.document())
        cursor.select(QTextCursor.Document)
        cursor.mergeCharFormat(fmt)

        # 3. Alignment & Wrap
        doc = self.document()
        option = doc.defaultTextOption()
        
        if self._wrap:
            option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            self.setTextWidth(800) # Default width for wrap
        else:
            option.setWrapMode(QTextOption.NoWrap)
            self.setTextWidth(-1) # No limit
        
        if self._align == "center": option.setAlignment(Qt.AlignCenter)
        elif self._align == "right": option.setAlignment(Qt.AlignRight)
        else: option.setAlignment(Qt.AlignLeft)
            
        doc.setDefaultTextOption(option)

        # 4. Line Height
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.Document)
        block_fmt = QTextBlockFormat()
        line_height_type = QTextBlockFormat.ProportionalHeight.value
        block_fmt.setLineHeight(self._line_height * 100, line_height_type)
        cursor.mergeBlockFormat(block_fmt)
        
        # 5. Shadow Effect
        if self._shadow_enabled:
            eff = QGraphicsDropShadowEffect()
            eff.setBlurRadius(self._shadow_blur)
            eff.setOffset(self._shadow_x, self._shadow_y)
            eff.setColor(QColor(self._shadow_color))
            self.setGraphicsEffect(eff)
        else:
            self.setGraphicsEffect(None)

        self.adjustSize()

    def paint(self, painter, option, widget=None):
        if option.state & QStyle.State_HasFocus:
            option.state &= ~QStyle.State_HasFocus
        super().paint(painter, option, widget)
        
        if self.isSelected():
            painter.setPen(QPen(QColor("#ff00cc"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def itemChange(self, change, value):
        return super().itemChange(change, value)
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._emit_changes()

    def _emit_changes(self):
        props = {
            "x": self.x(),
            "y": self.y(),
            "rotation": self.rotation(),
            "scale": int(self.scale() * 100)
        }
        self.sig_transform_changed.emit(self.layer_id, props)

    def update_transform(self, props: dict):
        self.update_properties(props)

    def update_properties(self, props: dict, z_index: int = None):
        # Transform
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "rotation" in props: self.setRotation(props["rotation"])
        if "start_time" in props: self.start_time = float(props["start_time"])
        
        # Content
        if "text_content" in props: 
            self.setPlainText(props["text_content"])
            self._apply_style() 

        # Style & Decor updates
        refresh = False
        
        keys_to_check = [
            "font_family", "font_size", "text_color", "text_weight", "text_italic", "text_wrap",
            "text_align", "line_height", "letter_spacing",
            "stroke_enabled", "stroke_color", "stroke_width",
            "shadow_enabled", "shadow_color", "shadow_blur", "shadow_x", "shadow_y"
        ]
        
        # Map props ke internal var
        if "font_family" in props: self._font_family = props["font_family"]; refresh = True
        if "font_size" in props: self._font_size = int(props["font_size"]); refresh = True
        if "text_color" in props: self._color = props["text_color"]; refresh = True
        if "text_weight" in props: self._weight = props["text_weight"]; refresh = True
        if "text_italic" in props: self._italic = props["text_italic"]; refresh = True
        if "text_wrap" in props: self._wrap = props["text_wrap"]; refresh = True
        
        if "text_align" in props: self._align = props["text_align"]; refresh = True
        if "line_height" in props: self._line_height = float(props["line_height"]); refresh = True
        if "letter_spacing" in props: self._letter_spacing = int(props["letter_spacing"]); refresh = True
        
        if "stroke_enabled" in props: self._stroke_enabled = props["stroke_enabled"]; refresh = True
        if "stroke_color" in props: self._stroke_color = props["stroke_color"]; refresh = True
        if "stroke_width" in props: self._stroke_width = int(props["stroke_width"]); refresh = True
        
        if "shadow_enabled" in props: self._shadow_enabled = props["shadow_enabled"]; refresh = True
        if "shadow_color" in props: self._shadow_color = props["shadow_color"]; refresh = True
        if "shadow_blur" in props: self._shadow_blur = int(props["shadow_blur"]); refresh = True
        if "shadow_x" in props: self._shadow_x = int(props["shadow_x"]); refresh = True
        if "shadow_y" in props: self._shadow_y = int(props["shadow_y"]); refresh = True
            
        if refresh:
            self._apply_style()

        if z_index is not None:
            self.setZValue(z_index)

    def sync_frame(self, t: float, video_service=None):
        pass