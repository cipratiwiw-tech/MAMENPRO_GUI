import os
from PySide6.QtGui import (QImage, QPixmap, QColor, QBrush, QPen, QFont, 
                           QPainter, QTextOption, QPainterPath, QFontMetrics, QRadialGradient)
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsBlurEffect
from PySide6.QtCore import Qt, QRectF, QPointF

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
        self.duration_s = 0.0

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
            
        # [BARU] Variable untuk status Drag & Drop Highlight
        self.is_drop_target = False

    # --- SINKRONISASI GEOMETRI ---
    def itemChange(self, change, value):
        """Otomatis update koordinat di settings saat item digeser di canvas"""
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.settings["x"] = int(self.pos().x())
            self.settings["y"] = int(self.pos().y())
        if change == QGraphicsItem.ItemRotationHasChanged:
            self.settings["frame_rot"] = int(self.rotation())
        return super().itemChange(change, value)

    # --- RENDERING UTAMA ---
    def paint(self, painter, option, widget):
        painter.save()
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        
        # 1. Masking Content agar tidak keluar dari Frame Rect
        # Kita gunakan save/restore tambahan di sini agar clipping hanya berefek pada konten
        painter.save()
        path = QPainterPath()
        path.addRect(self.rect())
        painter.setClipPath(path)
        
        # Placeholder jika media kosong
        if not self.current_pixmap:
            painter.setBrush(QColor(40, 40, 40, 150))
            painter.drawRect(self.rect())

        # 2. Gambar Konten (Media atau Teks)
        if self.current_pixmap and not self.current_pixmap.isNull():
            is_text = self.settings.get("content_type") == "text"
            painter.setOpacity(self.settings.get("opacity", 100) / 100.0)

            if is_text:
                # Teks digambar apa adanya
                painter.drawPixmap(0, 0, self.current_pixmap)
            else:
                # Media menggunakan transformasi Scale & Content Rotation
                scale = self.settings.get("scale", 100) / 100.0
                content_rot = self.settings.get("rot", 0)
                
                img_w = self.current_pixmap.width()
                img_h = self.current_pixmap.height()
                
                painter.translate(self.rect().center())
                painter.rotate(content_rot)
                painter.scale(scale, scale)
                painter.translate(-img_w/2, -img_h/2)
                painter.drawPixmap(0, 0, self.current_pixmap)
        
        # Restore pertama untuk melepas Clipping Path & Transformasi Konten
        painter.restore() 

        # 3. [MODIFIKASI] Border & Handle Seleksi
        # Tambahkan logika visual untuk Drop Target
        if hasattr(self, 'is_drop_target') and self.is_drop_target:
            # Highlight Merah/Oranye Tebal saat file ditahan di atas item ini
            pen = QPen(QColor("#ff9f43"), 4)
            pen.setJoinStyle(Qt.MiterJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.rect())
            
            # Label "DROP HERE" / "LEPAS DI SINI"
            painter.setPen(QColor("white"))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(12) # Ukuran disesuaikan
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "LEPAS DI SINI")

        elif self.isSelected() and not self.settings.get("lock", False): 
            # Hanya muncul jika item dipilih dan tidak dikunci
            self._paint_ui_helpers(painter)
            
        # Restore terakhir untuk painter.save() yang paling atas
        painter.restore()

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

    def mouseReleaseEvent(self, event):
        self.is_resizing = False
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mouseReleaseEvent(event)

    # --- KONTEN MEDIA & TEKS ---
    def set_content(self, path):
        self.file_path = path
        self.settings["content_type"] = "media"
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg', '.png', '.jpeg', '.webp', '.bmp']:
            self.current_pixmap = QPixmap(path)
        else:
            self._load_as_video(path)
        self.update()

    def set_text_content(self, text, is_paragraph=False):
        self.settings.update({
            "content_type": "text", "text_content": text, "is_paragraph": is_paragraph
        })
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
                self.duration_s = getattr(self.clip, 'duration', 0.0)
                self.seek_to(0)
            except Exception as e:
                print(f"Error load video: {e}")

    def seek_to(self, t):
        if self.clip:
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

# --- CLASS BACKGROUND ---
class BackgroundItem(VideoItem):
    """
    Spesialisasi VideoItem untuk latar belakang. 
    Mengisi seluruh canvas dan mendukung efek Blur/Vignette.
    """
    def __init__(self, path, scene_rect):
        super().__init__("BG", path, None)
        self.setZValue(-500) # Selalu paling bawah
        self.scene_w = scene_rect.width()
        self.scene_h = scene_rect.height()
        
        self.blur_effect = QGraphicsBlurEffect()
        self.setGraphicsEffect(self.blur_effect)
        self.settings.update({"blur": 0, "vig": 0, "is_bg": True})

    def update_bg_settings(self, data):
        self.settings.update(data)
        if "blur" in data:
            self.blur_effect.setBlurRadius(data["blur"])
        self.update()

    def paint(self, painter, option, widget):
        if not self.current_pixmap: return
        
        painter.save()
        s = self.settings
        img_w, img_h = self.current_pixmap.width(), self.current_pixmap.height()
        
        # Background Rendering (Centered Scaling)
        painter.translate(self.scene_w/2 + s["x"], self.scene_h/2 + s["y"])
        painter.scale(s["scale"]/100.0, s["scale"]/100.0)
        painter.translate(-img_w/2, -img_h/2)
        painter.drawPixmap(0, 0, self.current_pixmap)
        
        # Vignette Effect
        if s.get("vig", 0) > 0:
            grad = QRadialGradient(img_w/2, img_h/2, max(img_w, img_h)/1.5)
            grad.setColorAt(0, QColor(0,0,0,0))
            grad.setColorAt(1, QColor(0,0,0, int(s["vig"] * 2.55)))
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, img_w, img_h)
            
        painter.restore()

    def boundingRect(self):
        # Memperluas area agar background tetap terlihat meski di-zoom out
        m = 2000
        return QRectF(-m, -m, self.scene_w + m*2, self.scene_h + m*2)