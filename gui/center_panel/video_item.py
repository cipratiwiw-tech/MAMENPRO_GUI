import os
import math
from PySide6.QtGui import (QImage, QPixmap, QColor, QBrush, QPen, QFont, 
                           QPainter, QTextOption, QPainterPath, QFontMetrics, 
                           QRadialGradient, QLinearGradient, QTransform)
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsBlurEffect, QGraphicsPixmapItem
from PySide6.QtCore import Qt, QRectF, QPointF, QSizeF

# Import PyAVClip jika tersedia
try:
    from engine.pyav_engine import PyAVClip
except ImportError:
    PyAVClip = None

class VideoItem(QGraphicsRectItem):
    """
    Item utama untuk Media (Video/Gambar) dan Teks pada Canvas.
    """
    HANDLE_SIZE = 12
    # --- DEFINISI HANDLES ---
    Handles = {
        "NONE": 0, "TL": 1, "TM": 2, "TR": 3,
        "ML": 4, "MR": 5, "BL": 6, "BM": 7, "BR": 8
    }

    def __init__(self, name, file_path=None, parent=None, shape="portrait"):
        # Default Dimensions
        w, h = 540, 960
        if shape == "landscape": w, h = 960, 540 
        elif shape == "square": w, h = 720, 720
        
        super().__init__(0, 0, w, h, parent)
        
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        self.name = name
        self.file_path = file_path
        
        # --- INISIALISASI VARIABEL STATE ---
        self.is_in_time_range = True
        self.is_resizing = False
        self.current_handle = self.Handles["NONE"]
        self.resize_start_pos = None
        self.resize_start_rect = None
        self.is_drop_target = False
        
        self.start_time = 0.0
        self.end_time = 5.0
        self.source_duration = 0.0 # Default value
        
        self.settings = {
            "x": 0, "y": 0, 
            "frame_w": int(w), "frame_h": int(h), "frame_rot": 0, 
            "lock": False,
            "scale": 100, 
            "rot": 0,
            "opacity": 100,
            "sf_l": 0, "sf_r": 0, 
            "f_l": 0, "f_r": 0, "f_t": 0, "f_b": 0, # Feather 4 Sisi
            "shape": shape, 
            "content_type": "media", # Default
            "start_time": self.start_time,
            "end_time": self.end_time,
            "chroma_key": "#00ff00",
            "similarity": 100, "smoothness": 10,
            "spill_r": 0, "spill_g": 0, "spill_b": 0
        }

        self.current_pixmap = None 
        self.clip = None

        # --- LOGIKA IDENTIFIKASI KONTEN (PATCH APPLIED) ---
        # 1. Cek Media (Video/Image)
        if file_path and (file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')) or 
                          file_path.lower().endswith(('.jpg', '.png', '.jpeg', '.webp', '.bmp'))):
            self.settings["content_type"] = "media"
            
            # Logic load clip (dari kode asli)
            if PyAVClip:
                try:
                    self.clip = PyAVClip(file_path)
                    self.end_time = self.clip.duration
                    self.settings["end_time"] = self.end_time
                    self.source_duration = self.clip.duration
                except Exception as e:
                    print(f"[VideoItem] Error loading clip: {e}")

        # 2. Cek Text Layer biasa
        elif name.startswith("Text Layer"):
            self.settings["content_type"] = "text"
            self.settings["text_content"] = "New Text"
            self._update_text_pixmap()
            
        # 3. [BARU] Identifikasi Layer Caption Dummy
        elif name == "CAPTION_LAYER":
            self.settings["content_type"] = "caption_preview"
            self.settings["text_content"] = "CAPTION PREVIEW AREA"
            self.settings["lock"] = False # Harus bisa didrag
            self.settings["is_bg"] = False
            self.settings["font_size"] = 40
            self.settings["text_color"] = "#ffffff"
            self._update_text_pixmap()

    def _update_text_pixmap(self):
        # Fallback render sederhana untuk inisialisasi awal
        pm = QPixmap(1000, 200)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setPen(Qt.white)
        font = QFont("Arial", 60, QFont.Bold)
        p.setFont(font)
        p.drawText(pm.rect(), Qt.AlignCenter, self.settings.get("text_content", "Text"))
        p.end()
        self.current_pixmap = pm 
   

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.settings["x"] = value.x()
            self.settings["y"] = value.y()
        return super().itemChange(change, value)

    # --- LOGIKA RENDERING (VISIBILITY) ---
    def paint(self, painter, option, widget):
        # 1. Cek Status
        should_draw_content = self.is_in_time_range
        is_selected = self.isSelected()
        
        # Jika tidak aktif dan tidak dipilih -> Invisible total
        if not should_draw_content and not is_selected:
            return 

        # Simpan state painter utama
        painter.save() 
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        
        # 2. GAMBAR KONTEN
        if should_draw_content:
            # Masking agar tidak keluar dari Frame Rect
            path = QPainterPath()
            path.addRect(self.rect())
            painter.setClipPath(path)
            
            # Placeholder Background
            if not self.current_pixmap:
                painter.setBrush(QColor(40, 40, 40, 255))
                painter.drawRect(self.rect())

            # Gambar Pixmap
            if self.current_pixmap and not self.current_pixmap.isNull():
                painter.save() # <--- Simpan State
                try:           
                    opacity = self.settings.get("opacity", 100) / 100.0
                    painter.setOpacity(opacity)

                    is_text = self.settings.get("content_type") == "text"
                    # [BARU] Anggap caption sama seperti text cara gambarnya
                    is_caption = self.settings.get("content_type") == "caption_preview"

                    if is_text or is_caption:
                        # Render text/caption pixmap langsung (tanpa transformasi media kompleks)
                        painter.drawPixmap(self.rect().toRect(), self.current_pixmap)
                    else:
                        # --- LOGIKA MEDIA (Video/Image) ---
                        scale = self.settings.get("scale", 100) / 100.0
                        content_rot = self.settings.get("rot", 0)
                        
                        sf_l = self.settings.get("sf_l", 0)
                        sf_r = self.settings.get("sf_r", 0)
                        
                        f_l = self.settings.get("f_l", 0)
                        f_r = self.settings.get("f_r", 0)
                        f_t = self.settings.get("f_t", 0)
                        f_b = self.settings.get("f_b", 0)
                        
                        orig_w = self.current_pixmap.width()
                        orig_h = self.current_pixmap.height()
                        
                        src_x = sf_l
                        src_y = 0
                        src_w = max(1, orig_w - sf_l - sf_r)
                        src_h = orig_h
                        
                        # Transformasi
                        painter.translate(self.rect().center())
                        painter.rotate(content_rot)
                        painter.scale(scale, scale)
                        painter.translate(-src_w / 2, -src_h / 2)

                        # --- LOGIKA FEATHER ---
                        has_feather = (f_l > 0 or f_r > 0 or f_t > 0 or f_b > 0)

                        if not has_feather:
                            painter.drawPixmap(0, 0, self.current_pixmap, src_x, src_y, src_w, src_h)
                        else:
                            # Render ke Layer Sementara (Temp Pixmap)
                            temp_pm = QPixmap(src_w, src_h)
                            temp_pm.fill(Qt.transparent)
                            
                            p_temp = QPainter(temp_pm)
                            try:
                                # 1. Gambar Video Asli ke Temp
                                p_temp.drawPixmap(0, 0, self.current_pixmap, src_x, src_y, src_w, src_h)
                                
                                # 2. Hapus pinggiran (Feather) pakai DestinationOut
                                p_temp.setCompositionMode(QPainter.CompositionMode_DestinationOut)
                                
                                # -- Kiri --
                                if f_l > 0:
                                    grad = QLinearGradient(0, 0, f_l, 0)
                                    grad.setColorAt(0, QColor(0, 0, 0, 255)) 
                                    grad.setColorAt(1, QColor(0, 0, 0, 0))
                                    p_temp.fillRect(0, 0, f_l, src_h, grad)
                                
                                # -- Kanan --
                                if f_r > 0:
                                    grad = QLinearGradient(src_w - f_r, 0, src_w, 0)
                                    grad.setColorAt(0, QColor(0, 0, 0, 0))
                                    grad.setColorAt(1, QColor(0, 0, 0, 255))
                                    p_temp.fillRect(src_w - f_r, 0, f_r, src_h, grad)
                                
                                # -- Atas --
                                if f_t > 0:
                                    grad = QLinearGradient(0, 0, 0, f_t)
                                    grad.setColorAt(0, QColor(0, 0, 0, 255))
                                    grad.setColorAt(1, QColor(0, 0, 0, 0))
                                    p_temp.fillRect(0, 0, src_w, f_t, grad)
                                
                                # -- Bawah --
                                if f_b > 0:
                                    grad = QLinearGradient(0, src_h - f_b, 0, src_h)
                                    grad.setColorAt(0, QColor(0, 0, 0, 0))
                                    grad.setColorAt(1, QColor(0, 0, 0, 255))
                                    p_temp.fillRect(0, src_h - f_b, src_w, f_b, grad)
                                    
                            finally:
                                p_temp.end()
                            
                            # 3. Gambar hasil feather ke Main Painter
                            painter.drawPixmap(0, 0, temp_pm)

                finally:
                    painter.restore() # Restore state painter utama

            painter.setClipping(False)
            
        # 3. UI Helper (Selection, Handles, dll)
        if self.is_drop_target:
            pen = QPen(QColor("#ff9f43"), 4); pen.setJoinStyle(Qt.MiterJoin)
            painter.setPen(pen); painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.rect())
            painter.setPen(QColor("white"))
            painter.drawText(self.rect(), Qt.AlignCenter, "LEPAS DI SINI")

        elif is_selected and not self.settings.get("lock", False): 
            self._paint_ui_helpers(painter)
            if not should_draw_content:
                painter.setBrush(QBrush(QColor(255, 255, 255, 20), Qt.FDiagPattern))
                painter.setPen(Qt.NoPen)
                painter.drawRect(self.rect())
                painter.setPen(QColor("#ff5555"))
                painter.drawText(self.rect().topLeft() + QPointF(5, -5), "OFF")

        painter.restore()
    
    # --- LOGIKA WAKTU ---
    def set_time_range(self, start, duration=None):
        self.start_time = max(0.0, float(start))
        if duration is not None:
            dur = max(0.1, float(duration)) 
            self.end_time = self.start_time + dur
        else:
            self.end_time = None
            
        self.settings["start_time"] = self.start_time
        self.settings["end_time"] = self.end_time

    def apply_global_time(self, t_global):
        # 1. Cek apakah layer aktif di detik ini
        in_range = (t_global >= self.start_time)
        if self.end_time is not None:
            in_range = in_range and (t_global <= self.end_time)
        
        self.is_in_time_range = in_range

        # Agar item TIDAK PERNAH DESELECT otomatis.
        self.setVisible(True) 
        
        # 2. Update Frame Video jika aktif
        if in_range:
            t_local = t_global - self.start_time
            self.seek_to(t_local)
        
        self.update() # Trigger repaint
        
    # --- KONTEN MEDIA & TEKS ---
    def set_content(self, path):
        self.file_path = path
        self.settings["content_type"] = "media"
        ext = os.path.splitext(path)[1].lower()
        
        # 1. Cek Tipe File
        if ext in ['.jpg', '.png', '.jpeg', '.webp', '.bmp']:
            # IMAGE: Default 5 Detik
            self.current_pixmap = QPixmap(path)
            self.source_duration = 5.0 
        else:
            # VIDEO: Load dan ambil durasi asli
            self._load_as_video(path)
            
        # 2. Set durasi layer sesuai file asli
        final_dur = self.source_duration if self.source_duration > 0 else 5.0
        self.set_time_range(self.start_time, final_dur)
          
        self.update()

    def set_text_content(self, text, is_paragraph=False):
        text_defaults = {
            "content_type": "text",
            "text_content": text,
            "is_paragraph": is_paragraph,
            # Style Defaults
            "font": "Segoe UI",
            "font_size": 40,
            "text_color": "#ffffff",
            "alignment": "center",
            "line_spacing": 100,
            "bg_on": False,
            "bg_color": "#000000",
            "stroke_on": False,
            "stroke_width": 0,
            "stroke_color": "#000000",
            "shadow_on": False,
            "shadow_color": "#000000"
        }
        
        # Masukkan default jika key belum ada
        for k, v in text_defaults.items():
            if k not in self.settings:
                self.settings[k] = v

        # Update konten utama
        self.settings.update({
            "content_type": "text", 
            "text_content": text, 
            "is_paragraph": is_paragraph
        })
        
        # Text default duration 5s
        self.set_time_range(self.start_time, 5.0)
        self.refresh_text_render()

    def refresh_text_render(self):
        """Me-render teks menjadi QPixmap agar performa preview lancar"""
        s = self.settings
        w, h = max(1, int(self.rect().width())), max(1, int(self.rect().height()))
        
        canvas = QImage(w, h, QImage.Format_ARGB32)
        canvas.fill(Qt.transparent)
        
        p = QPainter(canvas)
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        
        if s.get("bg_on", False):
             p.setBrush(QColor(s.get("bg_color", "#000000"))); p.setPen(Qt.NoPen)
             p.drawRect(0, 0, w, h)
            
        font = QFont(s.get("font", "Arial"), s.get("font_size", 40))
        p.setFont(font)
        
        if s.get("is_paragraph"):
            p.setPen(QColor(s.get("text_color", "#ffffff")))
            opt = QTextOption(Qt.AlignCenter if s.get("alignment") == "center" else Qt.AlignLeft)
            opt.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            p.drawText(QRectF(10, 10, w-20, h-20), s.get("text_content", ""), opt)
        else:
            # Render Teks Judul dengan Stroke
            fm = QFontMetrics(font)
            path = QPainterPath()
            txt = s.get("text_content", "")
            tw, th = fm.horizontalAdvance(txt), fm.capHeight()
            path.addText((w - tw)/2, (h + th)/2, font, txt)
            
            if s.get("stroke_on"):
                pen = QPen(QColor(s.get("stroke_color", "black")), s.get("stroke_width", 2))
                p.setPen(pen); p.drawPath(path)
            
            p.fillPath(path, QColor(s.get("text_color", "white")))
        
        p.end()
        self.current_pixmap = QPixmap.fromImage(canvas)
        self.update()

    # --- VIDEO ENGINE BRIDGE ---
    def _load_as_video(self, path):
        if PyAVClip:
            try:
                self.clip = PyAVClip(path)
                self.source_duration = getattr(self.clip, 'duration', 0.0) 
                self.seek_to(0)
                print(f"[VIDEO LOAD] Duration detected: {self.source_duration}s")
            except Exception as e:
                print(f"Error load video: {e}")
                self.source_duration = 0.0

    def seek_to(self, t):
        if self.clip:
            t = max(0, t)
            f = self.clip.get_frame_at(t)
            if f is not None:
                img = QImage(f.data, f.shape[1], f.shape[0], f.shape[2]*f.shape[1], QImage.Format_RGB888)
                self.current_pixmap = QPixmap.fromImage(img.copy())
                self.update()

    def _paint_ui_helpers(self, painter):
        r = self.rect()
        painter.setPen(QPen(QColor("#4cc9f0"), 1, Qt.DashLine))
        painter.drawRect(r)
        
        s = self.HANDLE_SIZE
        painter.setBrush(QColor("white"))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(r.right() - s/2, r.bottom() - s/2, s, s)
        
        painter.setBrush(QColor("#4cc9f0"))
        painter.drawRect(0, -20, r.width(), 20)
        painter.setPen(Qt.black)
        painter.drawText(QRectF(0, -20, r.width(), 20), Qt.AlignCenter, self.name)
   
    def set_drop_highlight(self, active):
        if self.is_drop_target != active:
            self.is_drop_target = active
            self.update()
            
    # --- INTERAKSI MOUSE (RESIZING) ---
    def _get_handle_at(self, pos):
        r = self.rect()
        s = self.HANDLE_SIZE
        if QRectF(r.right() - s/2, r.bottom() - s/2, s, s).contains(pos):
            return self.Handles["BR"]
        return self.Handles["NONE"]

    def hoverMoveEvent(self, event):
        if not self.settings["lock"]:
            handle = self._get_handle_at(event.pos())
            self.setCursor(Qt.SizeFDiagCursor if handle != self.Handles["NONE"] else Qt.SizeAllCursor)
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
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing:
            diff = self.mapFromScene(event.scenePos()) - self.mapFromScene(self.resize_start_pos)
            new_w = max(50, self.resize_start_rect.width() + diff.x())
            new_h = max(50, self.resize_start_rect.height() + diff.y())
            
            old_center_scene = self.mapToScene(self.rect().center())

            self.prepareGeometryChange()
            self.setRect(0, 0, new_w, new_h)
            
            self.settings["frame_w"], self.settings["frame_h"] = int(new_w), int(new_h)
            
            new_center_local = self.rect().center()
            self.setTransformOriginPoint(new_center_local)
            
            new_center_scene = self.mapToScene(new_center_local)
            
            offset = old_center_scene - new_center_scene
            self.moveBy(offset.x(), offset.y())

            if self.settings.get("is_paragraph"): 
                self.refresh_text_render()
            
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.is_resizing = False
        is_locked = self.settings.get("lock", False)
        if not is_locked:
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mouseReleaseEvent(event)

# [PENTING] Tambahkan import 'math'
import math
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsBlurEffect, QGraphicsPixmapItem
from PySide6.QtGui import QRadialGradient, QBrush, QColor, QTransform

# ... (Class VideoItem biarkan apa adanya) ...

class BackgroundItem(VideoItem):
    def __init__(self, path, scene_rect):
        super().__init__("BG", path, None)
        self.setZValue(-500)
        
        self.scene_w = scene_rect.width()
        self.scene_h = scene_rect.height()
        
        # --- 1. VISUAL SETUP (Container Logic) ---
        self.container = QGraphicsRectItem(self)
        self.container.setRect(0, 0, self.scene_w, self.scene_h)
        self.container.setPen(Qt.NoPen)
        self.container.setFlag(QGraphicsItem.ItemClipsChildrenToShape, True)

        # Blur pada container
        self.blur_effect = QGraphicsBlurEffect()
        self.container.setGraphicsEffect(self.blur_effect)
        self.blur_effect.setEnabled(False)

        # Gambar Konten
        self.pixmap_item = QGraphicsPixmapItem(self.container)
        self.pixmap_item.setTransformationMode(Qt.SmoothTransformation)

        # Vignette Overlay
        self.vignette_item = QGraphicsRectItem(self)
        self.vignette_item.setRect(0, 0, self.scene_w, self.scene_h)
        self.vignette_item.setPen(Qt.NoPen)
        self.vignette_item.setZValue(10)
        self.vignette_item.setVisible(False)
        self.vignette_item.setAcceptedMouseButtons(Qt.NoButton)

        # --- 2. SETTINGS ---
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setAcceptHoverEvents(True)
        
        self.settings.update({
            "is_bg": True,
            "scale": 100, "x": 0, "y": 0, 
            "fit": "cover",
            "lock": False,
            "blur": 0,
            
            # --- VIGNETTE PARAMETERS ---
            "vig_strength": 0.0,
            "vig_radius": 0.8,
            "vig_angle": 0.0
        })
        
        self._is_dragging = False
        
        if path: self.set_content(path)
        self.set_time_range(0, None)
        self._apply_lock_state()

    # --- CORE: ANTI LONCAT ---
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return QPointF(0, 0)
        return super(VideoItem, self).itemChange(change, value)

    def _get_handle_at(self, pos):
        return self.Handles["NONE"]

    def boundingRect(self):
        return QRectF(-50000, -50000, 100000, 100000)

    def paint(self, painter, option, widget):
        pass

    def set_scene_size(self, w, h):
        self.scene_w = w
        self.scene_h = h
        self.container.setRect(0, 0, w, h)
        self.vignette_item.setRect(0, 0, w, h)
        self._sync_visuals()

    def set_content(self, path):
        super().set_content(path)
        self.settings.update({"x": 0, "y": 0, "scale": 100, "fit": "cover"})
        if self.current_pixmap:
            self.pixmap_item.setPixmap(self.current_pixmap)
            w, h = self.current_pixmap.width(), self.current_pixmap.height()
            self.pixmap_item.setOffset(-w/2, -h/2)
        self._sync_visuals()

    def update_bg_settings(self, data):
        if "vig" in data and "vig_strength" not in data:
            data["vig_strength"] = float(data["vig"]) / 100.0

        self.settings.update(data)
        if "lock" in data:
            self._apply_lock_state()
        self._sync_visuals()

    def _apply_lock_state(self):
        is_locked = self.settings.get("lock", False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, not is_locked)
        self.setCursor(Qt.ArrowCursor if is_locked else Qt.OpenHandCursor)

    def _sync_visuals(self):
        if not self.current_pixmap: return
        s = self.settings
        cw, ch = self.scene_w, self.scene_h
        
        # 1. Scale & Posisi
        pw, ph = self.current_pixmap.width(), self.current_pixmap.height()
        base_scale = 1.0
        if pw > 0 and ph > 0:
            scale_w = cw / pw
            scale_h = ch / ph
            fit_mode = s.get("fit", "cover")
            if fit_mode == "contain": base_scale = min(scale_w, scale_h)
            else: base_scale = max(scale_w, scale_h)
        
        final_scale = base_scale * (s["scale"] / 100.0)
        center_x = cw / 2 + s.get("x", 0)
        center_y = ch / 2 + s.get("y", 0)

        self.pixmap_item.setScale(final_scale)
        self.pixmap_item.setPos(center_x, center_y)

        # 2. VIGNETTE
        strength = float(s.get("vig_strength", 0.0))
        if strength == 0 and s.get("vig", 0) > 0:
            strength = s.get("vig", 0) / 100.0

        if strength > 0.01:
            self.vignette_item.setVisible(True)
            
            radius_param = float(s.get("vig_radius", 0.8))
            angle_deg = float(s.get("vig_angle", 0.0))
            
            max_dim = max(cw, ch)
            grad_radius = max_dim * radius_param
            
            angle_rad = math.radians(angle_deg)
            offset_dist = max_dim * 0.3 
            
            focal_x = (cw / 2) - math.cos(angle_rad) * offset_dist
            focal_y = (ch / 2) - math.sin(angle_rad) * offset_dist
            
            grad = QRadialGradient(cw / 2, ch / 2, grad_radius, focal_x, focal_y)
            
            softness_val = 0.4 * max_dim
            start_fade_pos = (grad_radius - softness_val) / grad_radius
            start_fade_pos = max(0.0, min(0.99, start_fade_pos))
            
            color_dark = QColor(0, 0, 0, int(strength * 255))
            color_clear = QColor(0, 0, 0, 0)
            
            grad.setColorAt(0.0, color_clear)
            grad.setColorAt(start_fade_pos, color_clear)
            grad.setColorAt(1.0, color_dark)
            grad.setSpread(QRadialGradient.PadSpread)
            
            self.vignette_item.setBrush(QBrush(grad))
        else:
            self.vignette_item.setVisible(False)

        # 3. Blur
        b = s.get("blur", 0)
        if b > 0 and not self._is_dragging:
            if self.blur_effect.blurRadius() != b:
                self.blur_effect.setBlurRadius(b)
            self.blur_effect.setEnabled(True)
        else:
            self.blur_effect.setEnabled(False)

    # --- HANDLERS BG ---
    def mousePressEvent(self, event):
        if self.settings.get("lock", False): event.ignore(); return
        self._is_dragging = True
        self.setCursor(Qt.ClosedHandCursor)
        self.blur_effect.setEnabled(False)
        event.accept()

    def mouseMoveEvent(self, event):
        if self.settings.get("lock", False): event.ignore(); return
        if self._is_dragging:
            delta = event.scenePos() - event.lastScenePos()
            self.settings["x"] += delta.x()
            self.settings["y"] += delta.y()
            self._sync_visuals()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.settings.get("lock", False): event.ignore(); return
        self._is_dragging = False
        self.setCursor(Qt.OpenHandCursor)
        self._sync_visuals()
        if self.isSelected():
            self.setSelected(False)
            self.setSelected(True)
        super().mouseReleaseEvent(event)