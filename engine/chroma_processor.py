import cv2
import numpy as np
from PySide6.QtGui import QImage

class ChromaProcessor:
    @staticmethod
    def process_qimage(qimage: QImage, hex_color: str, threshold: float, softness: float = 0.1) -> QImage:
        """
        HSV-based Chroma Key dengan Strict Memory Copy & Direct Alpha Assignment.
        """
        if qimage.isNull(): return qimage

        # 1. Pastikan Format RGBA 
        qimage = qimage.convertToFormat(QImage.Format_RGBA8888)
        width = qimage.width()
        height = qimage.height()

        # 2. Akses Memori Pixel (Shared Memory)
        ptr = qimage.bits() 
        arr = np.array(ptr).reshape(height, width, 4) 
        
        # 3. Konversi ke HSV
        img_rgb = cv2.cvtColor(arr, cv2.COLOR_RGBA2RGB)
        img_hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)

        # 4. Target Color
        target_rgb = ChromaProcessor._hex_to_rgb(hex_color)
        target_pixel = np.uint8([[target_rgb]]) 
        target_hsv = cv2.cvtColor(target_pixel, cv2.COLOR_RGB2HSV)[0][0]
        h_target = int(target_hsv[0])

        # 5. Adaptive Hue Tolerance
        hue_tol = int(15 + threshold * 45) 
        
        lower_h = np.array([max(0, h_target - hue_tol), 40, 40])
        upper_h = np.array([min(179, h_target + hue_tol), 255, 255])
        
        # 6. Masking
        mask = cv2.inRange(img_hsv, lower_h, upper_h)

        if softness > 0:
            k_size = int(softness * 10) | 1 
            if k_size > 1:
                mask = cv2.GaussianBlur(mask, (k_size, k_size), 0)

        # 7. Alpha Calculation (Invert)
        # Putih (255) = Objek, Hitam (0) = Transparan
        alpha_mask = cv2.bitwise_not(mask)
        
        # ✅ FIX #1: SET ALPHA LANGSUNG (Overwrite)
        # Jangan di-AND dengan alpha lama. Kita mau 'bolongin' gambar ini.
        arr[:, :, 3] = alpha_mask.astype(np.uint8)

        # 8. Spill Suppression
        spill_area = (mask > 10) 
        arr[:, :, 1][spill_area] = np.clip(arr[:, :, 1][spill_area] * 0.7, 0, 255).astype(np.uint8)

        # ✅ FIX #2: DEEP COPY & RECREATE QIMAGE
        # Kita buat QImage baru dari buffer array yang sudah dimodifikasi.
        # .copy() MEMUTUS hubungan dengan memori lama -> Qt dipaksa render ulang.
        out_image = QImage(
            arr.data,
            width,
            height,
            width * 4,
            QImage.Format_RGBA8888
        ).copy() 

        return out_image

    @staticmethod
    def _hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        if len(hex_str) != 6: return (0, 255, 0)
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))