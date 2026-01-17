import cv2
from PySide6.QtGui import QPixmap, QImage, QColor

class VideoService:
    """
    Video Provider yang Instantiable.
    Agar RenderWorker bisa punya cache sendiri yang tidak diganggu oleh UI Preview.
    """
    def __init__(self):
        # Cache Reader: path -> cv2.VideoCapture
        # Disimpan di self (instance), bukan class level
        self._readers = {}

    def get_frame(self, path: str, local_time: float) -> QPixmap:
        """Mengembalikan QPixmap untuk UI Preview"""
        img = self._get_image_data(path, local_time)
        if img.isNull():
            return self._get_blank_pixmap()
        return QPixmap.fromImage(img)

    def get_frame_image(self, path: str, local_time: float) -> QImage:
        """[BARU] Mengembalikan QImage murni untuk Compositor/Render (Lebih Cepat)"""
        return self._get_image_data(path, local_time)

    def _get_image_data(self, path: str, local_time: float) -> QImage:
        if not path: return QImage()

        # 1. Dapatkan Reader (Instance Scope)
        cap = self._get_reader(path)
        if not cap: return QImage()

        # 2. Logic Seek & Read
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 30
        
        target_frame = int(local_time * fps)
        current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

        # Optimasi Seek
        if abs(target_frame - current_frame) > 1:
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

        success, frame = cap.read()
        if not success:
            return QImage()

        # 3. Convert BGR -> RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        
        # Buat QImage (Copy data agar aman)
        return QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

    def _get_reader(self, path):
        if path not in self._readers:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                return None
            self._readers[path] = cap
        return self._readers[path]
    
    def release_all(self):
        """Membersihkan resource (Penting untuk Render Worker selesai)"""
        for cap in self._readers.values():
            cap.release()
        self._readers.clear()

    @staticmethod
    def _get_blank_pixmap():
        pix = QPixmap(320, 180)
        pix.fill(QColor("#000000"))
        return pix

# --- GLOBAL INSTANCE UNTUK UI PREVIEW ---
# UI akan pakai ini. Render Worker akan buat instance baru ("VideoService()") sendiri.
PREVIEW_SERVICE = VideoService()