import os
from engine.pyav_engine import PyAVClip 
from PySide6.QtGui import (QImage, QPixmap, QColor, QBrush, QPen, QFont, 
                          QPainter, QTextOption, QPainterPath, QFontMetrics, QCursor)
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF

class VideoItem(QGraphicsRectItem):
    # Definisi Handle (Posisi)
    HANDLE_SIZE = 12
    Handles = {
        "TL": 0, "T": 1, "TR": 2,
        "L": 3, "R": 4,
        "BL": 5, "B": 6, "BR": 7,
        "NONE": -1
    }

    def __init__(self, name, file_path=None, parent=None, shape="portrait"):
        # Setup awal dimensi
        if shape == "landscape": w, h = 960, 540 
        elif shape == "square": w, h = 720, 720
        elif shape == "text": w, h = 400, 200 # Default paragraf
        else: w, h = 540, 960

        super().__init__(0, 0, w, h, parent)
        
        self.name = name 
        self.file_path = file_path
        self.current_pixmap = None 
        self.clip = None          
        self.duration_s = 0.0

        # State Interaksi
        self.current_handle = self.Handles["NONE"]
        self.is_resizing = False
        self.resize_start_pos = QPointF()
        self.resize_start_rect = QRectF()

        self.settings = {
            "x": 0, "y": 0, 
            "scale": 100, 
            "rot": 0,
            "opacity": 100,
            "frame_w": int(w), 
            "frame_h": int(h),
            "frame_rot": 0,
            "lock": False,
            "shape": shape,
            "content_type": "media",
            # Text Settings
            "is_paragraph": False,
            "text_content": "Teks Baru",
            "font": "Arial",
            "font_size": 60,
            "text_color": "#ffffff",
            "bg_on": False,
            "bg_color": "#000000",
            "stroke_on": False,
            "stroke_width": 2,
            "stroke_color": "#000000"
        }
        
        self.setFlags(QGraphicsRectItem.ItemIsMovable | 
                      QGraphicsRectItem.ItemIsSelectable |
                      QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True) # Untuk cursor berubah saat hover handle
        
        self.setBrush(QBrush(QColor(40, 40, 40, 150))) 
        self.setPen(QPen(QColor("#4cc9f0"), 2))        
        self.setZValue(1)
        self.setTransformOriginPoint(self.rect().center())
        
        if file_path:
            self.set_content(file_path)

    # ==========================
    # LOGIKA INTERAKSI MOUSE (HANDLES)
    # ==========================
    def hoverMoveEvent(self, event):
        if self.settings["lock"]: 
            self.setCursor(Qt.ArrowCursor)
            return
            
        handle = self._get_handle_at(event.pos())
        if handle == self.Handles["TL"] or handle == self.Handles["BR"]:
            self.setCursor(Qt.SizeFDiagCursor)
        elif handle == self.Handles["TR"] or handle == self.Handles["BL"]:
            self.setCursor(Qt.SizeBDiagCursor)
        elif handle == self.Handles["L"] or handle == self.Handles["R"]:
            self.setCursor(Qt.SizeHorCursor)
        elif handle == self.Handles["T"] or handle == self.Handles["B"]:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.SizeAllCursor) # Cursor Move biasa
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if self.settings["lock"]: return
        
        handle = self._get_handle_at(event.pos())
        if handle != self.Handles["NONE"]:
            # Mulai Resize
            self.is_resizing = True
            self.current_handle = handle
            self.resize_start_pos = event.scenePos()
            self.resize_start_rect = self.rect()
            # Disable movable sementara agar tidak geser saat resize
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
        else:
            # Move Biasa
            self.is_resizing = False
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing:
            self._interactive_resize(event.scenePos())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.is_resizing = False
        self.current_handle = self.Handles["NONE"]
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mouseReleaseEvent(event)

    def _get_handle_at(self, pos):
        # Cek apakah mouse di atas handle tertentu
        if not self.isSelected(): return self.Handles["NONE"]
        
        r = self.rect()
        s = self.HANDLE_SIZE
        hs = s / 2
        
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
            if h_rect.contains(pos):
                return h_code
        return self.Handles["NONE"]

    def _interactive_resize(self, curr_pos):
        # Hitung offset mouse
        diff = self.mapFromScene(curr_pos) - self.mapFromScene(self.resize_start_pos)
        
        old_r = self.resize_start_rect
        new_x, new_y = old_r.x(), old_r.y()
        new_w, new_h = old_r.width(), old_r.height()
        
        dx = diff.x()
        dy = diff.y()

        # Update geometri berdasarkan handle yang ditarik
        h = self.current_handle
        
        if h in [self.Handles["R"], self.Handles["TR"], self.Handles["BR"]]:
            new_w += dx
        if h in [self.Handles["L"], self.Handles["TL"], self.Handles["BL"]]:
            new_x += dx
            new_w -= dx
            
        if h in [self.Handles["B"], self.Handles["BL"], self.Handles["BR"]]:
            new_h += dy
        if h in [self.Handles["T"], self.Handles["TL"], self.Handles["TR"]]:
            new_y += dy
            new_h -= dy

        # Minimum Size
        if new_w < 50: new_w = 50
        if new_h < 50: new_h = 50

        # Terapkan
        self.prepareGeometryChange()
        self.setRect(0, 0, new_w, new_h) # Reset ke 0,0 lokal
        # Update posisi item di scene jika resize dari kiri/atas
        # (Fitur ini agak kompleks di QGraphicsItem tanpa transform, 
        #  simplifikasinya: kita update settings width/height dulu)
        
        self.settings["frame_w"] = new_w
        self.settings["frame_h"] = new_h
        
        # PENTING: Jika Paragraf, Resize = Reflow Text
        if self.settings.get("is_paragraph"):
            self.refresh_text_render()
        # Jika Judul/Video, Resize = Scaling (Opsional, saat ini kita ubah Frame-nya saja)
        # User biasanya expect scaling font kalau judul, tapi agar konsisten 
        # kita biarkan frame membesar (seperti text box PowerPoint).
        
        self.setTransformOriginPoint(self.rect().center())
        self.update()


    # ==========================
    # LOGIKA KONTEN & TEXT
    # ==========================
    def set_content(self, path):
        self.file_path = path
        if not path: return
        self.settings["content_type"] = "media"
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
            self._load_as_image(path)
        else:
            self._load_as_video(path)

    def set_text_content(self, text, is_paragraph=False):
        self.file_path = None
        self.clip = None
        self.settings["content_type"] = "text"
        self.settings["text_content"] = text
        self.settings["is_paragraph"] = is_paragraph
        self.settings["font_size"] = 40 if is_paragraph else 80
        self.settings["bg_on"] = False
        self.duration_s = 5.0
        
        # Default Size Rect
        if is_paragraph:
            self.setRect(0, 0, 400, 300) # Box awal paragraf
        else:
            self.setRect(0, 0, 500, 150) # Box awal judul
        
        self.settings["frame_w"] = self.rect().width()
        self.settings["frame_h"] = self.rect().height()
        
        self.refresh_text_render()

    def refresh_text_render(self):
        """Render teks ke QPixmap dengan dukungan Stroke yang Benar"""
        if self.settings.get("content_type") != "text": return
        
        text = self.settings.get("text_content", "")
        is_para = self.settings.get("is_paragraph", False)
        
        font_family = self.settings.get("font", "Arial")
        font_size = self.settings.get("font_size", 60)
        color = self.settings.get("text_color", "#ffffff")
        stroke_on = self.settings.get("stroke_on", False)
        stroke_w = self.settings.get("stroke_width", 0)
        stroke_col = self.settings.get("stroke_color", "#000000")
        bg_on = self.settings.get("bg_on", False)
        bg_col = self.settings.get("bg_color", "#000000")
        
        # Dimensi Rect Item
        w = int(self.rect().width())
        h = int(self.rect().height())
        if w <= 0: w = 100
        if h <= 0: h = 100
        
        img = QImage(w, h, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # 1. Draw Background Box
        if bg_on:
            painter.setBrush(QColor(bg_col))
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, w, h)
        
        # Setup Font
        font = QFont(font_family, font_size, QFont.Bold if not is_para else QFont.Normal)
        painter.setFont(font)
        
        # Area text dengan padding
        padding = 10
        text_rect = QRectF(padding, padding, w - 2*padding, h - 2*padding)
        
        # --- LOGIC DRAWING TEXT WITH STROKE ---
        path = QPainterPath()
        
        if is_para:
            # --- Mode Paragraf (Multiline) ---
            # Menggunakan painter.drawText biasa karena QPainterPath untuk multiline sangat kompleks
            # Stroke di mode paragraf kita simulasikan dengan menggambar ulang (teknik brute force)
            # atau abaikan stroke untuk paragraf demi performa.
            # Disini kita pakai teknik simple: Fill Only untuk Paragraf, atau Outline standar
            
            option = QTextOption()
            option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            alignment_map = {
                "left": Qt.AlignLeft, "center": Qt.AlignCenter, 
                "right": Qt.AlignRight, "justify": Qt.AlignJustify
            }
            align_str = self.settings.get("alignment", "left")
            option.setAlignment(alignment_map.get(align_str, Qt.AlignLeft))

            painter.setPen(QColor(color))
            painter.drawText(text_rect, text, option)
            
        else:
            # --- Mode Judul (Single Line / Headline) ---
            # Menggunakan QPainterPath untuk hasil Stroke terbaik
            
            # Hitung posisi agar Center Vertikal & Horizontal
            fm = QFontMetrics(font)
            tw = fm.horizontalAdvance(text)
            th = fm.capHeight() # Tinggi huruf kapital
            
            # Koordinat start (Baseline)
            cx = (w - tw) / 2
            cy = (h + th) / 2 
            
            # Tambahkan Teks ke Path
            path.addText(cx, cy, font, text)
            
            # 1. Gambar Stroke (Jika aktif)
            if stroke_on and stroke_w > 0:
                pen = QPen(QColor(stroke_col))
                pen.setWidth(stroke_w)
                pen.setJoinStyle(Qt.RoundJoin)
                
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)
            
            # 2. Gambar Fill (Isi Teks)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(color))
            painter.drawPath(path)
            
        painter.end()
        self.current_pixmap = QPixmap.fromImage(img)
        self.update()
        
        
        
    # ==========================
    # PAINT & RENDER ITEM
    # ==========================
    def paint(self, painter, option, widget):
        # 1. Gambar Konten Utama (Pixmap)
        painter.save()
        # Clip area sesuai rect (kotak)
        path = QPainterPath()
        path.addRect(self.rect())
        painter.setClipPath(path)
        
        if self.current_pixmap and not self.current_pixmap.isNull():
            # Teks & Paragraf digambar Stretch/Fill ke rect?
            # Karena refresh_text_render sudah membuat pixmap SEUKURAN rect, kita draw 0,0
            if self.settings.get("content_type") == "text":
                painter.drawPixmap(0, 0, self.current_pixmap)
            else:
                # Video/Image Logic (Center Fit/Fill)
                # Disini kita gambar pixmap video di tengah
                img_w = self.current_pixmap.width()
                img_h = self.current_pixmap.height()
                # Center image
                cx = (self.rect().width() - img_w * (self.settings["scale"]/100)) / 2
                cy = (self.rect().height() - img_h * (self.settings["scale"]/100)) / 2
                
                painter.translate(self.rect().center())
                painter.scale(self.settings["scale"]/100, self.settings["scale"]/100)
                painter.translate(-img_w/2, -img_h/2)
                painter.setOpacity(self.settings["opacity"] / 100.0)
                painter.drawPixmap(0, 0, self.current_pixmap)
        else:
            # Placeholder jika kosong
            painter.setBrush(QColor(50, 50, 50, 100))
            painter.drawRect(self.rect())
            
        painter.restore()

        # 2. Gambar Boundary & Handles (Jika Terseleksi)
        if self.isSelected() and not self.settings["lock"]:
            self._paint_handles(painter)

        # 3. Label Nama
        if self.isSelected(): self._paint_label(painter)

    def _paint_handles(self, painter):
        r = self.rect()
        painter.setPen(QPen(QColor("#4cc9f0"), 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(r)
        
        # Gambar 8 kotak handle
        s = self.HANDLE_SIZE
        hs = s/2
        handles_pos = [
            QPointF(r.left(), r.top()), QPointF(r.center().x(), r.top()), QPointF(r.right(), r.top()),
            QPointF(r.right(), r.center().y()), QPointF(r.right(), r.bottom()), QPointF(r.center().x(), r.bottom()),
            QPointF(r.left(), r.bottom()), QPointF(r.left(), r.center().y())
        ]
        
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QColor("white"))
        for p in handles_pos:
            painter.drawRect(QRectF(p.x()-hs, p.y()-hs, s, s))

    # Helper standar lainnya (load_image, load_video, dll)
    # ... (Copy paste method _load_as_image, _load_as_video, seek_to dari kode sebelumnya) ...
    # Saya ringkas agar muat, tapi pastikan fungsi dasar media loading tetap ada.
    
    def _load_as_image(self, path):
        pix = QPixmap(path)
        self.current_pixmap = pix; self.update()
    def _load_as_video(self, path):
        self.clip = PyAVClip(path)
        self.seek_to(0)
    def seek_to(self, t):
        if self.clip:
            f = self.clip.get_frame_at(t)
            if f is not None:
                img = QImage(f.data, f.shape[1], f.shape[0], f.shape[2]*f.shape[1], QImage.Format_RGB888)
                self.current_pixmap = QPixmap.fromImage(img.copy())
                self.update()

    def update_from_settings(self, data):
        self.prepareGeometryChange()
        if "frame_w" in data: 
            self.setRect(0,0, data["frame_w"], data["frame_h"])
            self.setTransformOriginPoint(self.rect().center())
        
        self.settings.update(data)
        if "x" in data: self.setPos(data["x"], data["y"])
        if "frame_rot" in data: self.setRotation(data["frame_rot"])
        self.update()

    def _paint_label(self, painter):
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#4cc9f0"))
        painter.drawRect(0, -20, self.rect().width(), 20)
        painter.setPen(Qt.black)
        painter.drawText(QRectF(0, -20, self.rect().width(), 20), Qt.AlignCenter, self.name)
        painter.restore()

# BackgroundItem tetap sama seperti sebelumnya
class BackgroundItem(VideoItem):
    def __init__(self, path, scene_rect):
        super().__init__("BG", path, None)
        self.setZValue(-500) # Pastikan di belakang
        self.settings["is_bg"] = True
    def paint(self, painter, option, widget):
        if self.current_pixmap:
            painter.drawPixmap(self.settings["x"], self.settings["y"], self.current_pixmap)
    def boundingRect(self): return QRectF(0,0,1920,1080)