import cv2
from PySide6.QtGui import QPixmap, QImage, QColor

class VideoService:
    """
    Video Provider Single Instance.
    Menangani pembacaan frame dari file fisik berdasarkan Path atau Layer ID.
    """
    def __init__(self):
        # Cache Reader: path -> cv2.VideoCapture
        self._readers = {}
        # Map ID -> Path (Agar UI bisa request by ID)
        self._id_map = {}

    def register_source(self, layer_id: str, path: str):
        """Mendaftarkan source file untuk layer tertentu"""
        if not path: return
        
        self._id_map[layer_id] = path
        # Pre-load reader agar siap
        self._get_reader(path)
        print(f"[VideoService] Registered: {layer_id} -> {path}")

    def unregister_source(self, layer_id: str):
        """Melepas asosiasi ID dengan path"""
        if layer_id in self._id_map:
            del self._id_map[layer_id]
            # Note: Kita tidak langsung close reader (cap.release) karena
            # path yang sama mungkin dipakai layer lain.
            # Cleanup dilakukan di release_all().
            print(f"[VideoService] Unregistered: {layer_id}")

    def get_preview_frame(self, layer_id: str, local_time: float) -> QPixmap:
        """API Utama untuk PreviewPanel (By ID)"""
        path = self._id_map.get(layer_id)
        if not path:
            return self._get_blank_pixmap()
        return self.get_frame(path, local_time)

    def get_frame(self, path: str, local_time: float) -> QPixmap:
        """Mengembalikan QPixmap dari path (Internal/Direct)"""
        img = self._get_image_data(path, local_time)
        if img.isNull():
            return self._get_blank_pixmap()
        return QPixmap.fromImage(img)

    def get_frame_image(self, path: str, local_time: float) -> QImage:
        """Mengembalikan QImage murni untuk Compositor/Render"""
        return self._get_image_data(path, local_time)

    def _get_image_data(self, path: str, local_time: float) -> QImage:
        if not path: return QImage()

        cap = self._get_reader(path)
        if not cap: return QImage()

        # Logic Seek & Read
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 30
        
        target_frame = int(local_time * fps)
        current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

        # Optimasi: Hanya seek jika selisih frame signifikan (>1)
        if abs(target_frame - current_frame) > 1:
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

        success, frame = cap.read()
        if not success:
            return QImage()

        # Convert BGR (OpenCV) -> RGB (Qt)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        
        # QImage(data, width, height, bytesPerLine, format)
        # .copy() penting agar data tidak hilang saat garbage collection numpy
        return QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

    def _get_reader(self, path):
        if path not in self._readers:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                print(f"[VideoService] Failed to open: {path}")
                return None
            self._readers[path] = cap
        return self._readers[path]
    
    def release_all(self):
        """Membersihkan semua resource reader"""
        for cap in self._readers.values():
            cap.release()
        self._readers.clear()
        self._id_map.clear()

    @staticmethod
    def _get_blank_pixmap():
        pix = QPixmap(320, 180)
        pix.fill(QColor("#000000"))
        return pix