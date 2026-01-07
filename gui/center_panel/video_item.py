import os
from engine.pyav_engine import PyAVClip 
from PySide6.QtGui import (QImage, QPixmap, QColor, QBrush, QPen, QFont, 
                          QPainter, QTextOption, QPainterPath, QFontMetrics, QCursor, QRadialGradient)
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsBlurEffect
from PySide6.QtCore import Qt, QRectF, QPointF

class VideoItem(QGraphicsRectItem):
    HANDLE_SIZE = 12
    Handles = {
        "TL": 0, "T": 1, "TR": 2, "L": 3, "R": 4,
        "BL": 5, "B": 6, "BR": 7, "NONE": -1
    }

    def __init__(self, name, file_path=None, parent=None, shape="portrait"):
        if shape == "landscape": w, h = 960, 540 
        elif shape == "square": w, h = 720, 720
        elif shape == "text": w, h = 400, 200 
        else: w, h = 540, 960

        super().__init__(0, 0, w, h, parent)
        
        self.name = name 
        self.file_path = file_path
        self.current_pixmap = None 
        self.clip = None          
        self.duration_s = 0.0

        self.current_handle = self.Handles["NONE"]
        self.is_resizing = False
        self.resize_start_pos = QPointF()
        self.resize_start_rect = QRectF()

        self.settings = {
            "x": 0, "y": 0, "scale": 100, "rot": 0, "opacity": 100,
            "frame_w": int(w), "frame_h": int(h), "frame_rot": 0, "lock": False,
            "shape": shape, "content_type": "media",
            "is_paragraph": False, "text_content": "Teks Baru", "font": "Arial", "font_size": 60,
            "text_color": "#ffffff", "bg_on": False, "bg_color": "#000000",
            "stroke_on": False, "stroke_width": 2, "stroke_color": "#000000",
            "shadow_on": False, "shadow_color": "#555555"
        }
        
        self.setFlags(QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True) 
        self.setBrush(QBrush(QColor(40, 40, 40, 150))) 
        self.setPen(QPen(QColor("#4cc9f0"), 2))        
        self.setZValue(1)
        
        # ANCHOR POINT: Selalu dari center
        self.setTransformOriginPoint(self.rect().center())
        
        if file_path: self.set_content(file_path)

    def hoverMoveEvent(self, event):
        if self.settings["lock"]: 
            self.setCursor(Qt.ArrowCursor); return
        handle = self._get_handle_at(event.pos())
        if handle in [self.Handles["TL"], self.Handles["BR"]]: self.setCursor(Qt.SizeFDiagCursor)
        elif handle in [self.Handles["TR"], self.Handles["BL"]]: self.setCursor(Qt.SizeBDiagCursor)
        elif handle in [self.Handles["L"], self.Handles["R"]]: self.setCursor(Qt.SizeHorCursor)
        elif handle in [self.Handles["T"], self.Handles["B"]]: self.setCursor(Qt.SizeVerCursor)
        else: self.setCursor(Qt.SizeAllCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if self.settings["lock"]: return
        handle = self._get_handle_at(event.pos())
        if handle != self.Handles["NONE"]:
            self.is_resizing = True
            self.current_handle = handle
            self.resize_start_pos = event.scenePos()
            self.resize_start_rect = self.rect()
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
        else:
            self.is_resizing = False
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing: self._interactive_resize(event.scenePos())
        else: super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.is_resizing = False
        self.current_handle = self.Handles["NONE"]
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mouseReleaseEvent(event)

    def _get_handle_at(self, pos):
        if not self.isSelected(): return self.Handles["NONE"]
        r = self.rect()
        s = self.HANDLE_SIZE; hs = s / 2
        handles = {
            self.Handles["TL"]: QRectF(r.left()-hs, r.top()-hs, s, s),
            self.Handles["T"]:  QRectF(r.center().x()-hs, r.top()-hs, s, s),
            self.Handles["TR"]: QRectF(r.right()-hs, r.top()-hs, s, s),
            self.Handles["R"]:  QRectF(r.right()-hs, r.center().y()-hs, s, s),
            self.Handles["BR"]: QRectF(r.right()-hs, r.bottom()-hs, s, s),
            self.Handles["B"]:  QRectF(r.center().x()-hs, r.bottom()-hs, s, s),
            self.Handles["BL"]: QRectF(r.left()-hs, r.bottom()-hs, s, s),
            self.Handles["L"]:  QRectF(r.left()-hs, r.center().y()-hs, s, s),
        }
        for h_code, h_rect in handles.items():
            if h_rect.contains(pos): return h_code
        return self.Handles["NONE"]

    def _interactive_resize(self, curr_pos):
        diff = self.mapFromScene(curr_pos) - self.mapFromScene(self.resize_start_pos)
        old_r = self.resize_start_rect
        new_w, new_h = old_r.width(), old_r.height()
        dx, dy = diff.x(), diff.y()
        h = self.current_handle
        
        if h in [self.Handles["R"], self.Handles["TR"], self.Handles["BR"]]: new_w += dx
        if h in [self.Handles["L"], self.Handles["TL"], self.Handles["BL"]]: new_w -= dx
        if h in [self.Handles["B"], self.Handles["BL"], self.Handles["BR"]]: new_h += dy
        if h in [self.Handles["T"], self.Handles["TL"], self.Handles["TR"]]: new_h -= dy

        if new_w < 50: new_w = 50
        if new_h < 50: new_h = 50

        self.prepareGeometryChange()
        self.setRect(0, 0, new_w, new_h)
        self.settings["frame_w"] = new_w
        self.settings["frame_h"] = new_h
        
        if self.settings.get("is_paragraph"): self.refresh_text_render()
        
        # PENTING: Update Center Anchor setelah Resize
        self.setTransformOriginPoint(self.rect().center())
        self.update()

    def set_content(self, path):
        self.file_path = path
        if not path: return
        self.settings["content_type"] = "media"
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']: self._load_as_image(path)
        else: self._load_as_video(path)

    def set_text_content(self, text, is_paragraph=False):
        self.file_path = None; self.clip = None
        self.settings["content_type"] = "text"
        self.settings["text_content"] = text
        self.settings["is_paragraph"] = is_paragraph
        self.settings["font_size"] = 40 if is_paragraph else 80
        self.settings["bg_on"] = False
        self.duration_s = 5.0
        
        if is_paragraph: self.setRect(0, 0, 400, 300)
        else: self.setRect(0, 0, 500, 150)
        
        self.settings["frame_w"] = self.rect().width()
        self.settings["frame_h"] = self.rect().height()
        # Update Anchor
        self.setTransformOriginPoint(self.rect().center())
        self.refresh_text_render()

    def refresh_text_render(self):
        if self.settings.get("content_type") != "text": return
        text = self.settings.get("text_content", "")
        is_para = self.settings.get("is_paragraph", False)
        font_family = self.settings.get("font", "Arial")
        font_size = self.settings.get("font_size", 60)
        color = self.settings.get("text_color", "#ffffff")
        stroke_on = self.settings.get("stroke_on", False); stroke_w = self.settings.get("stroke_width", 0); stroke_col = self.settings.get("stroke_color", "#000000")
        bg_on = self.settings.get("bg_on", False); bg_col = self.settings.get("bg_color", "#000000")
        shadow_on = self.settings.get("shadow_on", False); shadow_col = self.settings.get("shadow_color", "#555555")

        w = int(self.rect().width()); h = int(self.rect().height())
        if w <= 0: w = 100; h = 100
        
        img = QImage(w, h, QImage.Format_ARGB32); img.fill(Qt.transparent)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing); painter.setRenderHint(QPainter.TextAntialiasing)
        
        if bg_on:
            painter.setBrush(QColor(bg_col)); painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, w, h)
        
        font = QFont(font_family, font_size, QFont.Bold if not is_para else QFont.Normal)
        painter.setFont(font)
        padding = 10; text_rect = QRectF(padding, padding, w - 2*padding, h - 2*padding)
        path = QPainterPath()
        
        if is_para:
            option = QTextOption(); option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            align = self.settings.get("alignment", "left")
            amap = {"left": Qt.AlignLeft, "center": Qt.AlignCenter, "right": Qt.AlignRight, "justify": Qt.AlignJustify}
            option.setAlignment(amap.get(align, Qt.AlignLeft))
            painter.setPen(QColor(color))
            painter.drawText(text_rect, text, option)
        else:
            fm = QFontMetrics(font); tw = fm.horizontalAdvance(text); th = fm.capHeight()
            cx = (w - tw) / 2; cy = (h + th) / 2 
            path.addText(cx, cy, font, text)
            if shadow_on:
                painter.translate(5, 5); painter.setPen(Qt.NoPen); painter.setBrush(QColor(shadow_col))
                painter.drawPath(path); painter.translate(-5, -5)
            if stroke_on and stroke_w > 0:
                pen = QPen(QColor(stroke_col)); pen.setWidth(stroke_w); pen.setJoinStyle(Qt.RoundJoin)
                painter.setPen(pen); painter.setBrush(Qt.NoBrush); painter.drawPath(path)
            painter.setPen(Qt.NoPen); painter.setBrush(QColor(color)); painter.drawPath(path)
            
        painter.end()
        self.current_pixmap = QPixmap.fromImage(img)
        self.update()

    def paint(self, painter, option, widget):
        painter.save()
        path = QPainterPath(); path.addRect(self.rect()); painter.setClipPath(path)
        
        if self.current_pixmap and not self.current_pixmap.isNull():
            if self.settings.get("content_type") == "text":
                painter.setOpacity(self.settings["opacity"] / 100.0)
                painter.drawPixmap(0, 0, self.current_pixmap)
            else:
                img_w = self.current_pixmap.width(); img_h = self.current_pixmap.height()
                painter.translate(self.rect().center())
                painter.scale(self.settings["scale"]/100, self.settings["scale"]/100)
                painter.translate(-img_w/2, -img_h/2)
                painter.setOpacity(self.settings["opacity"] / 100.0)
                painter.drawPixmap(0, 0, self.current_pixmap)
        else:
            painter.setBrush(QColor(50, 50, 50, 100)); painter.drawRect(self.rect())
        painter.restore()

        if self.isSelected() and not self.settings["lock"]: self._paint_handles(painter)
        if self.isSelected(): self._paint_label(painter)

    def _paint_handles(self, painter):
        r = self.rect()
        painter.setPen(QPen(QColor("#4cc9f0"), 1, Qt.DashLine)); painter.setBrush(Qt.NoBrush); painter.drawRect(r)
        s = self.HANDLE_SIZE; hs = s/2
        handles_pos = [QPointF(r.left(), r.top()), QPointF(r.center().x(), r.top()), QPointF(r.right(), r.top()),
            QPointF(r.right(), r.center().y()), QPointF(r.right(), r.bottom()), QPointF(r.center().x(), r.bottom()),
            QPointF(r.left(), r.bottom()), QPointF(r.left(), r.center().y())]
        painter.setPen(QPen(Qt.black, 1)); painter.setBrush(QColor("white"))
        for p in handles_pos: painter.drawRect(QRectF(p.x()-hs, p.y()-hs, s, s))

    def _paint_label(self, painter):
        painter.save(); painter.setPen(Qt.NoPen); painter.setBrush(QColor("#4cc9f0"))
        painter.drawRect(0, -20, self.rect().width(), 20)
        painter.setPen(Qt.black); painter.drawText(QRectF(0, -20, self.rect().width(), 20), Qt.AlignCenter, self.name)
        painter.restore()

    def _load_as_image(self, path): pix = QPixmap(path); self.current_pixmap = pix; self.update()
    def _load_as_video(self, path): self.clip = PyAVClip(path); self.seek_to(0)
    def seek_to(self, t):
        if self.clip:
            f = self.clip.get_frame_at(t)
            if f is not None:
                img = QImage(f.data, f.shape[1], f.shape[0], f.shape[2]*f.shape[1], QImage.Format_RGB888)
                self.current_pixmap = QPixmap.fromImage(img.copy()); self.update()

    def update_from_settings(self, data):
        self.prepareGeometryChange()
        if "frame_w" in data: 
            self.setRect(0,0, data["frame_w"], data["frame_h"])
            self.setTransformOriginPoint(self.rect().center())
        
        self.settings.update(data)
        if "x" in data: self.setPos(data["x"], data["y"])
        if "frame_rot" in data: self.setRotation(data["frame_rot"])
        self.update()

class BackgroundItem(VideoItem):
    def __init__(self, path, scene_rect):
        super().__init__("BG", path, None)
        self.setZValue(-500) 
        self.settings["is_bg"] = True
        self.settings.update({"x": 0, "y": 0, "scale": 100, "blur": 0, "vig": 0})
        self.blur_effect = QGraphicsBlurEffect()
        self.setGraphicsEffect(self.blur_effect)
        self.blur_effect.setBlurRadius(0)

    def update_bg_settings(self, data):
        self.settings.update(data)
        # Efek Blur Realtime
        b = data.get("blur", 0)
        self.blur_effect.setBlurRadius(b)
        self.update() 

    def paint(self, painter, option, widget):
        if self.current_pixmap and not self.current_pixmap.isNull():
            painter.save()
            x = self.settings.get("x", 0)
            y = self.settings.get("y", 0)
            scale = self.settings.get("scale", 100) / 100.0
            vig_val = self.settings.get("vig", 0)

            painter.translate(x, y)
            painter.scale(scale, scale)
            painter.drawPixmap(0, 0, self.current_pixmap)
            
            # Efek Vignette (Visual Overlay)
            if vig_val > 0:
                # Gambar gradient radial hitam transparan di atas background
                # Kita perlu rect sebesar pixmap aslinya
                pw, ph = self.current_pixmap.width(), self.current_pixmap.height()
                gradient = QRadialGradient(pw/2, ph/2, max(pw, ph)/1.5)
                # Tengah transparan, Pinggir hitam
                gradient.setColorAt(0, QColor(0,0,0,0))
                gradient.setColorAt(1 - (vig_val/200.0), QColor(0,0,0, int(vig_val * 2.55))) 
                painter.setBrush(QBrush(gradient))
                painter.setPen(Qt.NoPen)
                painter.drawRect(0, 0, pw, ph)

            painter.restore()

    def boundingRect(self):
        return QRectF(-50000, -50000, 100000, 100000)