from PySide6.QtGui import QPixmap

class BackgroundService:
    @staticmethod
    def calculate_bg_geometry(pixmap: QPixmap, canvas_rect):
        """Menghitung scale dan posisi background (Logic Aspect Ratio)"""
        if not pixmap:
            return None
            
        bg_w = pixmap.width()
        bg_h = pixmap.height()
        canvas_w = canvas_rect.width()
        canvas_h = canvas_rect.height()
        
        final_scale = 100
        pos_x = 0
        pos_y = 0
        is_bg_portrait = bg_h > bg_w
        
        if is_bg_portrait:
            scale_w = canvas_w / bg_w
            scale_h = canvas_h / bg_h
            final_scale = max(scale_w, scale_h) * 100
            new_w = bg_w * (final_scale / 100)
            new_h = bg_h * (final_scale / 100)
            pos_x = (canvas_w - new_w) / 2
            pos_y = (canvas_h - new_h) / 2
        else:
            scale_h = canvas_h / bg_h
            final_scale = scale_h * 100
            new_w = bg_w * (final_scale / 100)
            pos_x = (canvas_w - new_w) / 2
            pos_y = 0

        return {
            'scale': int(final_scale),
            'x': int(pos_x),
            'y': int(pos_y)
        }