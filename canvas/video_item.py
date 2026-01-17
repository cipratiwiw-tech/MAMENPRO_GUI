# canvas/video_item.py
from PySide6.QtCore import QObject, Signal, Qt, QPointF
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtGui import QPixmap, QColor, QPen

# Import Gizmo
try:
    from gui.center_panel.canvas_items.transform_gizmo import TransformGizmo
except ImportError:
    TransformGizmo = None

class VideoLayerItem(QObject, QGraphicsPixmapItem): 
    sig_transform_changed = Signal(str, dict)

    def __init__(self, layer_id, path, parent=None):
        QObject.__init__(self)
        QGraphicsPixmapItem.__init__(self, parent)
        
        self.gizmo = None
        self.setTransformationMode(Qt.SmoothTransformation)
        
        self.layer_id = layer_id
        self.file_path = path
        self.start_time = 0.0
        
        self.setZValue(0) 

        # --- INTERAKSI ---
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges 
        )
        
        # PENTING: Origin point di tengah agar rotasi porosnya benar
        self.setTransformOriginPoint(self.boundingRect().center())
        self._set_placeholder()

    def _set_placeholder(self):
        pix = QPixmap(320, 180)
        pix.fill(QColor("#333333"))
        self.setPixmap(pix)
        self._update_origin()

    def _update_origin(self):
        rect = self.boundingRect()
        self.setTransformOriginPoint(rect.center())
        if self.gizmo:
            self.gizmo._update_layout()

    # --- 🔥 LOGIKA SNAP BARU (CENTER ANCHOR) 🔥 ---
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = QPointF(value) # Posisi Top-Left calon (sebelum diterapkan)
            parent = self.parentItem()
            
            if parent and hasattr(parent, 'show_guide_vertical'):
                # 1. Ambil Ukuran Clip (dikali scale)
                rect = self.boundingRect()
                current_scale = self.scale()
                
                # Ukuran real clip di layar
                clip_w = rect.width() * current_scale
                clip_h = rect.height() * current_scale
                
                # 2. Hitung Titik Tengah Calon Clip (Anchor Point)
                # new_pos adalah sudut kiri atas. Jadi Center = TopLeft + 1/2 Ukuran
                clip_center_x = new_pos.x() + (clip_w / 2)
                clip_center_y = new_pos.y() + (clip_h / 2)
                
                # 3. Ambil Titik Tengah Canvas (Anchor Point)
                canvas_rect = parent.rect()
                canvas_center_x = canvas_rect.width() / 2
                canvas_center_y = canvas_rect.height() / 2
                
                # 4. Cek Jarak Snap (Threshold 25px agar terasa "menggigit")
                SNAP_DIST = 25.0
                
                is_snapped_x = False
                is_snapped_y = False
                
                # --- LOGIKA X (Vertikal Snap) ---
                if abs(clip_center_x - canvas_center_x) < SNAP_DIST:
                    # RUMUS KUNCI: Posisi Baru = Pusat Canvas - Setengah Clip
                    target_x = canvas_center_x - (clip_w / 2)
                    new_pos.setX(target_x)
                    is_snapped_x = True
                
                # --- LOGIKA Y (Horizontal Snap) ---
                if abs(clip_center_y - canvas_center_y) < SNAP_DIST:
                    target_y = canvas_center_y - (clip_h / 2)
                    new_pos.setY(target_y)
                    is_snapped_y = True
                
                # 5. Nyalakan/Matikan Garis Bantu
                parent.show_guide_vertical(is_snapped_x)
                parent.show_guide_horizontal(is_snapped_y)

            return new_pos

        # Matikan guide saat seleksi dilepas/berubah
        if change == QGraphicsItem.ItemSelectedChange:
            is_selected = bool(value)
            if is_selected:
                if not self.gizmo and TransformGizmo:
                    self.gizmo = TransformGizmo(self)
            else:
                if self.gizmo:
                    self.scene().removeItem(self.gizmo)
                    self.gizmo = None
                
                # Pastikan guide mati saat deselect
                parent = self.parentItem()
                if parent and hasattr(parent, 'show_guide_vertical'):
                    parent.show_guide_vertical(False)
                    parent.show_guide_horizontal(False)

        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        
        # Bersihkan guide setelah drag selesai
        parent = self.parentItem()
        if parent and hasattr(parent, 'show_guide_vertical'):
            parent.show_guide_vertical(False)
            parent.show_guide_horizontal(False)
            
        self._emit_changes()

    def sync_frame(self, t, video_service):
        if not video_service: return
        qimg = video_service.get_frame_image(self.file_path, t)
        if qimg and not qimg.isNull():
            self.setPixmap(QPixmap.fromImage(qimg))
            self._update_origin()

    def update_transform(self, props: dict):
        if "x" in props: self.setX(props["x"])
        if "y" in props: self.setY(props["y"])
        if "rotation" in props: self.setRotation(props["rotation"])
        if "scale" in props: self.setScale(props["scale"] / 100.0)
        if "opacity" in props: self.setOpacity(props["opacity"])

    def notify_transform_change(self):
        self._emit_changes()

    def _emit_changes(self):
        final_props = {
            "x": self.pos().x(),
            "y": self.pos().y(),
            "rotation": self.rotation(),
            "scale": int(self.scale() * 100)
        }
        self.sig_transform_changed.emit(self.layer_id, final_props)

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)