import os
from PySide6.QtGui import (QImage, QPixmap, QColor, QBrush, QPen, QFont, 
                           QPainter, QTextOption, QPainterPath, QFontMetrics, 
                           QRadialGradient, QLinearGradient) # [FIX] Import Wajib Ada
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsBlurEffect
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
    # --- [FIX 1] DEFINISI HANDLES (Wajib Ada) ---
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
        
        # --- [FIX 2] INISIALISASI VARIABEL STATE (Wajib Ada) ---
        self.is_in_time_range = True  # Default aktif agar terlihat saat baru di-add
        self.is_resizing = False
        self.current_handle = self.Handles["NONE"]
        self.resize_start_pos = None
        self.resize_start_rect = None
        self.is_drop_target = False
        
        self.start_time = 0.0
        self.end_time = 5.0
        
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
            "content_type": "media",
            "start_time": self.start_time,
            "end_time": self.end_time,
            "chroma_key": "#00ff00",
            "similarity": 100, "smoothness": 10,
            "spill_r": 0, "spill_g": 0, "spill_b": 0
        }

        self.current_pixmap = None 
        self.clip = None
        
        if file_path and PyAVClip:
            try:
                self.clip = PyAVClip(file_path)
                self.end_time = self.clip.duration
                self.settings["end_time"] = self.end_time
            except Exception as e:
                print(f"[VideoItem] Error loading clip: {e}")

        if name.startswith("Text Layer"):
            self.settings["content_type"] = "text"
            self.settings["text_content"] = "New Text"
            self._update_text_pixmap()

    def _update_text_pixmap(self):
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
        # 1. Cek Status (Sekarang aman karena variabel sudah di-init di __init__)
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
                try:           # <--- TAMBAHKAN BLOK TRY DISINI
                    is_text = self.settings.get("content_type") == "text"
                    opacity = self.settings.get("opacity", 100) / 100.0
                    painter.setOpacity(opacity)

                    if is_text:
                        painter.drawPixmap(self.rect().toRect(), self.current_pixmap)
                    else:
                        # --- LOGIKA MEDIA ---
                        # (Ambil variable scale, rot, sf_l, f_l, dll seperti sebelumnya...)
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
                            try: # Try-Finally untuk painter sementara
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
                                p_temp.end() # Wajib diakhiri
                            
                            # 3. Gambar hasil feather ke Main Painter
                            painter.drawPixmap(0, 0, temp_pm)

                finally:           # <--- TAMBAHKAN BLOK FINALLY DISINI
                    painter.restore() # <--- Pastikan Restore dijalankan apapun yg terjadi

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
        # [FIX] Inisialisasi nilai default agar tidak KeyError saat refresh_text_render
        text_defaults = {
            "font": "Segoe UI",
            "font_size": 40 if is_paragraph else 60,
            "text_color": "#ffffff",
            "bg_on": False,
            "bg_color": "#000000",
            "stroke_on": False,
            "stroke_width": 2,
            "stroke_color": "#000000",
            "alignment": "center",
            "line_spacing": 100
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
            # 1. Hitung selisih drag
            diff = self.mapFromScene(event.scenePos()) - self.mapFromScene(self.resize_start_pos)
            new_w = max(50, self.resize_start_rect.width() + diff.x())
            new_h = max(50, self.resize_start_rect.height() + diff.y())
            
            # --- [FIX 3] KOMPENSASI DRIFTING ORIGIN ---
            # Simpan posisi center LAMA (di koordinat scene)
            old_center_scene = self.mapToScene(self.rect().center())

            self.prepareGeometryChange()
            self.setRect(0, 0, new_w, new_h)
            
            # Update settings size
            self.settings["frame_w"], self.settings["frame_h"] = int(new_w), int(new_h)
            
            # Update origin ke center BARU
            new_center_local = self.rect().center()
            self.setTransformOriginPoint(new_center_local)
            
            # Hitung di mana center BARU sekarang berada di scene
            new_center_scene = self.mapToScene(new_center_local)
            
            # Geser item (pos) sebesar selisih pergeseran center
            # Ini membuat item tetap diam di tempat secara visual
            offset = old_center_scene - new_center_scene
            self.moveBy(offset.x(), offset.y())

            # --- [OPSIONAL] SYNC CONTENT SCALE (Agar gambar ikut membesar) ---
            # Jika user membesarkan kotak, gambar ikut membesar
            ratio_w = new_w / self.resize_start_rect.width()
            # ratio_h = new_h / self.resize_start_rect.height() # Bisa pilih salah satu atau rata-rata
            
            # Matikan baris di bawah ini jika ingin mode "Crop" (Kotak membesar, gambar tetap)
            # self.settings["scale"] = max(1, int(self.settings["scale"] * ratio_w))

            if self.settings.get("is_paragraph"): 
                self.refresh_text_render()
            
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