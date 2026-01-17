import cv2
import numpy as np
from PySide6.QtGui import QImage

class ChromaProcessor:
    @staticmethod
    def process_qimage(qimage: QImage, hex_color: str, threshold: float) -> QImage:
        """
        Menghapus background warna tertentu dari QImage.
        Menggunakan OpenCV (NumPy) agar performa Realtime.
        """
        if qimage.isNull(): return qimage

        # 1. Konversi QImage (RGB) -> NumPy Array
        # QImage Format harus RGB888 agar kompatibel
        qimage = qimage.convertToFormat(QImage.Format_RGB888)
        width = qimage.width()
        height = qimage.height()

        ptr = qimage.constBits()
        # Buat view numpy langsung ke memori QImage (Cepat!)
        arr = np.array(ptr).reshape(height, width, 3) # RGB format

        # 2. Parse Target Color (Hex -> RGB)
        target_color = ChromaProcessor._hex_to_rgb(hex_color)
        
        # 3. Buat Masking (Range Warna)
        # Threshold (0.0 - 1.0) dikonversi ke Range Pixel (0 - 255)
        thresh_val = int(threshold * 100) # Scale up sensitivity
        
        # Batas Bawah & Atas warna yang akan dihapus
        lower_bound = np.array([
            max(0, target_color[0] - thresh_val),
            max(0, target_color[1] - thresh_val),
            max(0, target_color[2] - thresh_val)
        ])
        upper_bound = np.array([
            min(255, target_color[0] + thresh_val),
            min(255, target_color[1] + thresh_val),
            min(255, target_color[2] + thresh_val)
        ])

        # 4. Deteksi area warna (Masking)
        mask = cv2.inRange(arr, lower_bound, upper_bound)

        # 5. Alpha Channel Trick
        # Kita butuh output RGBA (agar transparan).
        # Tambahkan channel Alpha ke array RGB
        r, g, b = cv2.split(arr)
        
        # Mask bernilai 255 (Putih) di area Hijau. 
        # Kita ingin Alpha = 0 di area Hijau, dan 255 di area lain.
        # Jadi kita Invert mask-nya.
        alpha = cv2.bitwise_not(mask)

        # Gabungkan lagi: R, G, B, Alpha
        rgba = cv2.merge([r, g, b, alpha])

        # 6. Kembalikan ke QImage
        # Format ARGB32 lebih aman untuk QPainter nanti
        output_qimage = QImage(rgba.data, width, height, QImage.Format_RGBA8888).copy()
        
        return output_qimage

    @staticmethod
    def _hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))