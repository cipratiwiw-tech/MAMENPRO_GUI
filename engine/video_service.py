# engine/video_service.py
import cv2
import os
from PySide6.QtGui import QPixmap, QImage, QColor
from engine.frame_cache import FrameCache

class VideoService:
    """
    Source provider untuk preview & render.
    - Video  : time-based (seconds → frame index via FPS metadata)
    - Image  : static frame (cached sekali)
    """

    def __init__(self):
        # path -> cv2.VideoCapture
        self._readers = {}
        # layer_id -> QImage (static image)
        self._image_cache = {}
        # layer_id -> path
        self._id_map = {}
        
        # Cache Frame Video (simpan 100 frame terakhir di RAM)
        self._video_frame_cache = FrameCache(max_frames=100)

    # ---------- REGISTRATION ----------

    def register_source(self, layer_id: str, path: str):
        if not path:
            return

        self._id_map[layer_id] = path
        ext = os.path.splitext(path)[1].lower()

        if ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
            img = cv2.imread(path)
            if img is not None:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                h, w, ch = img.shape
                qimg = QImage(
                    img.data, w, h, ch * w, QImage.Format_RGB888
                ).copy()
                self._image_cache[layer_id] = qimg
        else:
            self._get_reader(path)

    def unregister_source(self, layer_id: str):
        if layer_id in self._image_cache:
            del self._image_cache[layer_id]
        if layer_id in self._id_map:
            del self._id_map[layer_id]

    # ---------- PREVIEW API ----------

    def get_preview_frame(self, layer_id: str, local_time: float) -> QPixmap:
        if layer_id in self._image_cache:
            return QPixmap.fromImage(self._image_cache[layer_id])

        path = self._id_map.get(layer_id)
        if not path:
            return self._blank()

        img = self._get_image_by_time(path, local_time)
        if img.isNull():
            return self._blank()
        return QPixmap.fromImage(img)

    # ---------- RENDER / COMPOSITOR API ----------

    def get_frame_image(self, path: str, local_time: float) -> QImage:
        # [FIX] Guard clause: Jangan proses jika path kosong
        if not path:
            return QImage()
        return self._get_image_by_time(path, local_time)

    # ---------- INTERNAL ----------

    def _get_image_by_time(self, path: str, time_sec: float) -> QImage:
        # [FIX] Guard clause tambahan
        if not path:
            return QImage()

        # A. Cek Image Static Layer
        for lid, p in self._id_map.items():
            if p == path and lid in self._image_cache:
                return self._image_cache[lid]

        # B. Cek Cache Video di RAM
        cached_frame = self._video_frame_cache.get(time_sec)
        if cached_frame:
            return cached_frame

        # C. Jika tidak ada di cache, baru baca dari OpenCV
        cap = self._get_reader(path)
        if not cap:
            return QImage()

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            return QImage()

        target_frame = int(round(time_sec * fps))
        img = self._read_frame(cap, target_frame)
        
        # Simpan hasil baca ke Cache
        if not img.isNull():
            self._video_frame_cache.put(time_sec, img)
            
        return img

    def release_all(self):
        for cap in self._readers.values():
            cap.release()
        self._readers.clear()
        self._image_cache.clear()
        self._id_map.clear()
        self._video_frame_cache.clear()

    def _read_frame(self, cap, frame_index: int) -> QImage:
        current = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if abs(frame_index - current) > 1:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

        ok, frame = cap.read()
        if not ok:
            return QImage()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        return QImage(
            frame.data, w, h, ch * w, QImage.Format_RGB888
        ).copy()

    def _get_reader(self, path: str):
        # [FIX] Guard clause: Jangan buka OpenCV jika path kosong
        if not path:
            return None

        if path not in self._readers:
            try:
                cap = cv2.VideoCapture(path)
                if not cap.isOpened():
                    return None
                self._readers[path] = cap
            except Exception as e:
                print(f"Error opening video reader: {e}")
                return None
                
        return self._readers[path]

    @staticmethod
    def _blank():
        pix = QPixmap(320, 180)
        pix.fill(QColor("#000000"))
        return pix