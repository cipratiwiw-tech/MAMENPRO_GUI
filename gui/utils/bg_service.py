from PySide6.QtGui import QPixmap

class BackgroundService:
    @staticmethod
    def calculate_bg_geometry(pixmap: QPixmap, canvas_rect):
        """
        Menghitung scale dan posisi background agar:
        1. Fit to Center (Cover/Fill) tanpa Stretch.
        2. Selalu memenuhi canvas (Zoom In jika perlu).
        3. Koordinat X/Y dihitung dari Top-Left corner gambar setelah di-scale.
        """
        if not pixmap:
            return None
            
        bg_w = pixmap.width()
        bg_h = pixmap.height()
        canvas_w = canvas_rect.width()
        canvas_h = canvas_rect.height()
        
        # Hitung rasio scale untuk lebar dan tinggi
        scale_w = canvas_w / bg_w
        scale_h = canvas_h / bg_h
        
        # LOGIKA "COVER" / "FILL":
        # Ambil scale terbesar agar gambar menutupi seluruh canvas.
        # Ini otomatis menangani kasus "Landscape BG di Portrait Canvas" -> Zoom In.
        final_scale_factor = max(scale_w, scale_h)
        
        # Hitung dimensi akhir background setelah di-scale
        new_w = bg_w * final_scale_factor
        new_h = bg_h * final_scale_factor
        
        # Hitung Posisi (Centering)
        # Koordinat 0,0 canvas ada di kiri atas.
        # Jika gambar lebih besar dari canvas, posisi x/y akan minus (terpotong kiri/atas).
        pos_x = (canvas_w - new_w) / 2
        pos_y = (canvas_h - new_h) / 2

        return {
            'scale': int(final_scale_factor * 100), # Simpan dalam persen (int)
            'x': int(pos_x),
            'y': int(pos_y)
        }