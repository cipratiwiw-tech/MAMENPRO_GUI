import cv2
from PySide6.QtGui import QImage, QPixmap, QColor

class VideoService:
    """
    Singleton Service untuk decoding video.
    Menggunakan caching reader agar tidak buka-tutup file terus menerus (berat).
    """
    _instance = None
    _readers = {} # Cache: path -> cv2.VideoCapture

    @staticmethod
    def get_frame(path: str, local_time: float) -> QPixmap:
        """
        Mengambil frame pada detik ke-X dari file video.
        """
        if not path: return VideoService._get_blank_pixmap()

        # 1. Dapatkan Reader (Reuse jika sudah ada)
        cap = VideoService._get_reader(path)
        if not cap: return VideoService._get_blank_pixmap()

        # 2. Hitung Frame Number
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 30 # Fallback
        
        target_frame = int(local_time * fps)
        
        # 3. Optimasi Seeking (Loncat Frame)
        # Jika frame target == frame berikutnya, tidak perlu seek (langsung read)
        # Jika jauh, baru seek (karena seek itu mahal/lambat)
        current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if abs(target_frame - current_frame) > 1:
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

        # 4. Baca Frame
        success, frame = cap.read()
        if not success:
            return VideoService._get_blank_pixmap()

        # 5. Konversi OpenCV (BGR) -> Qt (RGB)
        # OpenCV pakai BGR, Qt pakai RGB. Harus dibalik.
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Kembalikan sebagai Pixmap (agar siap tampil di scene)
        return QPixmap.fromImage(qt_image)

    @classmethod
    def _get_reader(cls, path):
        if path not in cls._readers:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                return None
            cls._readers[path] = cap
        return cls._readers[path]

    @staticmethod
    def _get_blank_pixmap():
        # Fallback gambar hitam jika error/kosong
        pix = QPixmap(320, 180)
        pix.fill(QColor("#000000"))
        return pix