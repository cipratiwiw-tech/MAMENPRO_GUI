import cv2
import os
from PySide6.QtGui import QPixmap, QImage, QColor


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
        return self._get_image_by_time(path, local_time)

    # ---------- INTERNAL ----------

    def _get_image_by_time(self, path: str, time_sec: float) -> QImage:
        # image layer (static)
        for lid, p in self._id_map.items():
            if p == path and lid in self._image_cache:
                return self._image_cache[lid]

        cap = self._get_reader(path)
        if not cap:
            return QImage()

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            return QImage()

        target_frame = int(round(time_sec * fps))
        return self._read_frame(cap, target_frame)

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
        if path not in self._readers:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                return None
            self._readers[path] = cap
        return self._readers[path]

    def release_all(self):
        for cap in self._readers.values():
            cap.release()
        self._readers.clear()
        self._image_cache.clear()
        self._id_map.clear()

    @staticmethod
    def _blank():
        pix = QPixmap(320, 180)
        pix.fill(QColor("#000000"))
        return pix
