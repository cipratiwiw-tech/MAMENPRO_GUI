import os
from PySide6.QtGui import (QImage, QPixmap, QColor, QBrush, QPen, QFont, 
                           QPainter, QTextOption, QPainterPath, QFontMetrics, QRadialGradient)
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsBlurEffect
from PySide6.QtCore import Qt, QRectF, QPointF, QSizeF

# Import PyAVClip jika tersedia, jika tidak sediakan placeholder agar tidak crash
try:
    from engine.pyav_engine import PyAVClip
except ImportError:
    PyAVClip = None

class VideoItem(QGraphicsRectItem):
    """
    Item utama untuk Media (Video/Gambar) dan Teks pada Canvas.
    Mendukung seleksi, resizing manual, dan sinkronisasi settings ke UI.
    """
    HANDLE_SIZE = 12
    Handles = {
        "TL": 0, "T": 1, "TR": 2, "L": 3, "R": 4,
        "BL": 5, "B": 6, "BR": 7, "NONE": -1
    }

    def __init__(self, name, file_path=None, parent=None, shape="portrait"):
        # Default Dimensions berdasarkan Shape
        w, h = 540, 960
        if shape == "landscape": w, h = 960, 540 
        elif shape == "square": w, h = 720, 720
        elif shape == "text": w, h = 400, 200 

        super().__init__(0, 0, w, h, parent)
        
        self.name = name 
        self.file_path = file_path
        self.current_pixmap = None 
        self.clip = None      
            
        # [BARU] Atribut Waktu (Start & End)
        self.start_time = 0.0
        self.end_time = 5.0  # Default 5 detik awal
        self.source_duration = 0.0 # Durasi asli file sumber
        
        # [BARU] Status apakah layer sedang dalam rentang waktu tayang
        self.is_in_time_range = True

        self.current_handle = self.Handles["NONE"]
        self.is_resizing = False
        self.resize_start_pos = QPointF()
        self.resize_start_rect = QRectF()
        
        self.is_drop_target = False

        # Status Resizing
        self.current_handle = self.Handles["NONE"]
        self.is_resizing = False
        self.resize_start_pos = QPointF()
        self.resize_start_rect = QRectF()

        # --- DICTIONARY SETTINGS (Sumber data utama untuk Controller) ---
        self.settings = {
            "x": 0, "y": 0, 
            "frame_w": int(w), "frame_h": int(h), "frame_rot": 0, 
            "lock": False,
            "scale": 100, 
            "rot": 0,           # Rotasi konten di dalam frame
            "opacity": 100,
            "shape": shape, 
            "content_type": "media",
            
            # [BARU] Simpan info waktu ke settings agar bisa dirender/disave
            "start_time": self.start_time,
            "end_time": self.end_time,
            
            "is_paragraph": False, "text_content": "Teks Baru", "font": "Arial", "font_size": 60,
            "text_color": "#ffffff", "bg_on": False, "bg_color": "#000000",
            "stroke_on": False, "stroke_width": 2, "stroke_color": "#000000",
            "shadow_on": False, "shadow_color": "#555555",
            "alignment": "center"
        }
        
        # Konfigurasi Interaksi
        self.setFlags(QGraphicsRectItem.ItemIsMovable | 
                      QGraphicsRectItem.ItemIsSelectable | 
                      QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True) 
        self.setZValue(1)
        self.setTransformOriginPoint(self.rect().center())
        
        if file_path: 
            self.set_content(file_path)

    # --- SINKRONISASI GEOMETRI ---
    def itemChange(self, change, value):
        """Otomatis update koordinat di settings saat item digeser di canvas"""
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.settings["x"] = int(self.pos().x())
            self.settings["y"] = int(self.pos().y())
        if change == QGraphicsItem.ItemRotationHasChanged:
            self.settings["frame_rot"] = int(self.rotation())
        return super().itemChange(change, value)

    # --- LOGIKA RENDERING (VISIBILITY) ---
    def paint(self, painter, option, widget):
        # 1. Cek Status
        should_draw_content = self.is_in_time_range
        is_selected = self.isSelected()
        
        # Jika tidak aktif dan tidak dipilih -> Invisible total
        if not should_draw_content and not is_selected:
            return 

        painter.save()
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        
        # 2. GAMBAR KONTEN (HANYA JIKA DALAM DURASI)
        if should_draw_content:
            # Masking Content agar tidak keluar dari Frame Rect
            path = QPainterPath()
            path.addRect(self.rect())
            painter.setClipPath(path)
            
            # Placeholder (Kotak abu-abu jika pixmap kosong)
            if not self.current_pixmap:
                painter.setBrush(QColor(40, 40, 40, 255))
                painter.drawRect(self.rect())

            # Gambar Pixmap (Video/Gambar/Teks)
            if self.current_pixmap and not self.current_pixmap.isNull():
                is_text = self.settings.get("content_type") == "text"
                painter.setOpacity(self.settings.get("opacity", 100) / 100.0)

                if is_text:
                    painter.drawPixmap(0, 0, self.current_pixmap)
                else:
                    scale = self.settings.get("scale", 100) / 100.0
                    content_rot = self.settings.get("rot", 0)
                    
                    img_w = self.current_pixmap.width()
                    img_h = self.current_pixmap.height()
                    
                    painter.translate(self.rect().center())
                    painter.rotate(content_rot)
                    painter.scale(scale, scale)
                    painter.translate(-img_w/2, -img_h/2)
                    painter.drawPixmap(0, 0, self.current_pixmap)
            
            # Matikan clipping sebelum menggambar UI luar
            painter.setClipping(False)

        # 3. UI OVERLAY & SELECTION (SELALU GAMBAR JIKA SELECTED)
        # Ini akan menggambar kotak putus-putus meskipun konten tidak digambar (kosong)
        
        if self.is_drop_target:
            # Efek Drop Target
            pen = QPen(QColor("#ff9f43"), 4); pen.setJoinStyle(Qt.MiterJoin)
            painter.setPen(pen); painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.rect())
            painter.setPen(QColor("white")); font = painter.font(); font.setBold(True); font.setPointSize(12)
            painter.setFont(font); painter.drawText(self.rect(), Qt.AlignCenter, "LEPAS DI SINI")

        elif is_selected and not self.settings.get("lock", False): 
            # Gambar Border Putus-putus & Handle Resize
            self._paint_ui_helpers(painter)
            
            # [BARU] Tambahkan indikator visual jika layer sedang "Mati" (Di luar durasi)
            if not should_draw_content:
                # Arsir diagonal tipis agar user tau area frame-nya
                painter.setBrush(QBrush(QColor(255, 255, 255, 20), Qt.FDiagPattern))
                painter.setPen(Qt.NoPen)
                painter.drawRect(self.rect())
                
                # Label status
                painter.setPen(QColor("#ff5555")) # Merah terang
                painter.drawText(self.rect().topLeft() + QPointF(5, -5), f"OFF (Start: {self.start_time}s)")

        painter.restore()
    
    # --- [CORE FIX] LOGIKA WAKTU (TANPA SETVISIBLE FALSE) ---
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
        
        self.update() # Trigger repaint untuk update visual ghost/normal
        
    # --- KONTEN MEDIA & TEKS ---
    def set_content(self, path):
        self.file_path = path
        self.settings["content_type"] = "media"
        ext = os.path.splitext(path)[1].lower()
        
        # 1. Cek Tipe File
        if ext in ['.jpg', '.png', '.jpeg', '.webp', '.bmp']:
            # IMAGE: Default 5 Detik (Bisa diubah user nanti)
            self.current_pixmap = QPixmap(path)
            self.source_duration = 5.0 
        else:
            # VIDEO: Load dan ambil durasi asli
            self._load_as_video(path)
            
        # 2. [FIX UTAMA] Set durasi layer sesuai file asli
        # Jika source_duration 0 (gagal), fallback ke 5.0
        final_dur = self.source_duration if self.source_duration > 0 else 5.0
        self.set_time_range(self.start_time, final_dur)
          
        self.update()

    def set_text_content(self, text, is_paragraph=False):
        self.settings.update({
            "content_type": "text", "text_content": text, "is_paragraph": is_paragraph
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
        
        if s["bg_on"]:
            p.setBrush(QColor(s["bg_color"])); p.setPen(Qt.NoPen)
            p.drawRect(0, 0, w, h)
            
        font = QFont(s["font"], s["font_size"])
        p.setFont(font)
        
        if s["is_paragraph"]:
            p.setPen(QColor(s["text_color"]))
            opt = QTextOption(Qt.AlignCenter if s["alignment"] == "center" else Qt.AlignLeft)
            opt.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            p.drawText(QRectF(10, 10, w-20, h-20), s["text_content"], opt)
        else:
            # Render Teks Judul dengan Stroke jika aktif
            fm = QFontMetrics(font)
            path = QPainterPath()
            tw, th = fm.horizontalAdvance(s["text_content"]), fm.capHeight()
            path.addText((w - tw)/2, (h + th)/2, font, s["text_content"])
            
            if s.get("stroke_on"):
                pen = QPen(QColor(s["stroke_color"]), s["stroke_width"])
                p.setPen(pen); p.drawPath(path)
            
            p.fillPath(path, QColor(s["text_color"]))
        
        p.end()
        self.current_pixmap = QPixmap.fromImage(canvas)
        self.update()

    # --- VIDEO ENGINE BRIDGE ---
    def _load_as_video(self, path):
        if PyAVClip:
            try:
                self.clip = PyAVClip(path)
                # [FIX BUG] Gunakan variable yg konsisten (source_duration)
                # Sebelumnya pakai duration_s yg tidak dibaca set_content
                self.source_duration = getattr(self.clip, 'duration', 0.0) 
                self.seek_to(0)
                print(f"[VIDEO LOAD] Duration detected: {self.source_duration}s")
            except Exception as e:
                print(f"Error load video: {e}")
                self.source_duration = 0.0

    def seek_to(self, t):
        # [MODIFIKASI] Cek batas durasi sumber (Looping atau Stop)
        # Di sini kita pakai logika CLAMP (tahan di frame terakhir jika lewat)
        if self.clip:
            # Pastikan t tidak negatif
            t = max(0, t)
            # Opsional: Jika ingin looping video di dalam layer: t = t % self.source_duration
            
            f = self.clip.get_frame_at(t)
            if f is not None:
                img = QImage(f.data, f.shape[1], f.shape[0], f.shape[2]*f.shape[1], QImage.Format_RGB888)
                self.current_pixmap = QPixmap.fromImage(img.copy())
                self.update()

    def _paint_ui_helpers(self, painter):
        # Garis Border Dash
        r = self.rect()
        painter.setPen(QPen(QColor("#4cc9f0"), 1, Qt.DashLine))
        painter.drawRect(r)
        
        # Handle Kanan Bawah
        s = self.HANDLE_SIZE
        painter.setBrush(QColor("white"))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(r.right() - s/2, r.bottom() - s/2, s, s)
        
        # Label Nama Frame
        painter.setBrush(QColor("#4cc9f0"))
        painter.drawRect(0, -20, r.width(), 20)
        painter.setPen(Qt.black)
        painter.drawText(QRectF(0, -20, r.width(), 20), Qt.AlignCenter, self.name)
   
    def set_drop_highlight(self, active):
        if self.is_drop_target != active:
            self.is_drop_target = active
            self.update() # Trigger repaint
            
    # --- INTERAKSI MOUSE (RESIZING) ---
    def _get_handle_at(self, pos):
        """Cek apakah mouse berada di atas handle resize (kanan bawah)"""
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
            
            self.prepareGeometryChange()
            self.setRect(0, 0, new_w, new_h)
            self.settings["frame_w"], self.settings["frame_h"] = int(new_w), int(new_h)
            
            if self.settings.get("is_paragraph"): 
                self.refresh_text_render()
            
            self.setTransformOriginPoint(self.rect().center())
            self.update()
        else:
            super().mouseMoveEvent(event)

    # [FIX] Perbaikan Logic Mouse Release
    def mouseReleaseEvent(self, event):
        self.is_resizing = False
        
        # HANYA aktifkan kembali Movable JIKA item TIDAK dikunci
        is_locked = self.settings.get("lock", False)
        if not is_locked:
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            
        super().mouseReleaseEvent(event)

# --- CLASS BACKGROUND (VIGNETTE FIXED ON CANVAS) ---
class BackgroundItem(VideoItem):
    """
    Spesialisasi VideoItem untuk latar belakang.
    Fitur:
    - Auto Center
    - Fit Mode: 'cover' (Zoom Center)
    - Vignette STATIC (Tidak ikut geser saat BG digeser)
    - Sinkronisasi Drag & Typing Coordinate
    """
    def __init__(self, path, scene_rect):
        super().__init__("BG", path, None)
        self.setZValue(-500) 
        
        self.scene_w = scene_rect.width()
        self.scene_h = scene_rect.height()
        
        self.blur_effect = QGraphicsBlurEffect()
        self.setGraphicsEffect(self.blur_effect)
        
        # Default Settings
        self.settings.update({
            "blur": 0, "vig": 0, "is_bg": True, 
            "scale": 100, "x": 0, "y": 0, 
            "fit": "cover",
            "lock": False
        })
        
        self.blur_effect.setEnabled(False)
        self.set_time_range(0, None)

    def set_scene_size(self, w, h):
        self.scene_w = w
        self.scene_h = h
        self.update()

    # Di dalam class BackgroundItem
    def set_content(self, path):
        super().set_content(path)
        self.setPos(0, 0) 
        # Simpan state awal x,y = 0 di settings
        self.settings.update({"x": 0, "y": 0, "scale": 100, "fit": "cover"})
        self.update()

    def update_bg_settings(self, data):
        self.settings.update(data)
        
        # [FIX] Update Flag Movable Sesuai Status Lock
        if "lock" in data:
            is_locked = data["lock"]
            # Jika dikunci, matikan fitur Movable
            self.setFlag(QGraphicsItem.ItemIsMovable, not is_locked)
        
        if "x" in data or "y" in data:
            self.setPos(data.get("x", 0), data.get("y", 0))
            
        self.update()

    def paint(self, painter, option, widget):
        if not self.current_pixmap: 
            painter.fillRect(self.boundingRect(), Qt.black)
            return
        
        painter.save()
        s = self.settings
        
        cw, ch = self.scene_w, self.scene_h
        pw, ph = self.current_pixmap.width(), self.current_pixmap.height()
        
        # Ambil posisi fisik item saat ini (karena drag / setPos)
        curr_x = self.pos().x()
        curr_y = self.pos().y()

        # --- 1. GAMBAR KONTEN (IMAGE) ---
        # Logic Scale
        base_scale = 1.0
        if pw > 0 and ph > 0:
            scale_w = cw / pw
            scale_h = ch / ph
            fit_mode = s.get("fit", "cover")
            if fit_mode == "contain": base_scale = min(scale_w, scale_h)
            else: base_scale = max(scale_w, scale_h)

        final_scale = base_scale * (s["scale"] / 100.0)
        
        # Logic Transform
        # Kita HAPUS 'painter.translate(s["x"], s["y"])' manual
        # Karena posisi sudah ditangani oleh sistem Qt via self.pos()
        
        # Pindah ke Tengah Canvas (Relative terhadap Item Origin)
        painter.translate(cw / 2, ch / 2)
        
        # Scale
        painter.scale(final_scale, final_scale)
        
        # Geser Pivot Image ke Tengah
        painter.translate(-pw / 2, -ph / 2)
        
        # Draw Image
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, self.current_pixmap)
        
        painter.restore() # Restore ke koordinat item lokal (0,0 = item pos)

        # --- 2. VIGNETTE (STATIC ON CANVAS) ---
        if s.get("vig", 0) > 0:
            vig_strength = int(s["vig"] * 2.55)
            radius = max(cw, ch) / 1.2
            
            grad = QRadialGradient(cw / 2, ch / 2, radius)
            grad.setColorAt(0, QColor(0, 0, 0, 0))
            grad.setColorAt(1, QColor(0, 0, 0, vig_strength))
            
            # --- TEKNIK PENTING: KOMPENSASI POSISI ---
            # Kita 'mundurkan' painter sejauh posisi item saat ini.
            # Jadi (0,0) painter kembali pas di (0,0) Scene/Layar.
            painter.save()
            painter.translate(-curr_x, -curr_y) 
            
            painter.fillRect(0, 0, int(cw), int(ch), QBrush(grad))
            painter.restore()

    def boundingRect(self):
        return QRectF(-5000, -5000, 10000, 10000)