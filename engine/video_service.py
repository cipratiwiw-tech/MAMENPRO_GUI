# engine/video_service.py
import cv2
import numpy as np
from PySide6.QtGui import QPixmap, QImage, QColor
from engine.frame_cache import FrameCache

class VideoService:
    def __init__(self):
        self._readers = {}     
        self._image_cache = {} 
        self._id_map = {}      
        self._video_frame_cache = FrameCache(max_frames=100)

    # ---------- REGISTRATION ----------
    def register_source(self, layer_id: str, path: str):
        if not path: return
        self._id_map[layer_id] = path
        ext = path.split('.')[-1].lower()
        if ext in ["jpg", "jpeg", "png", "bmp", "webp"]:
            img = cv2.imread(path)
            if img is not None:
                self._image_cache[layer_id] = img 
        else:
            self._get_reader(path)

    def unregister_source(self, layer_id: str):
        if layer_id in self._image_cache: del self._image_cache[layer_id]
        if layer_id in self._id_map: del self._id_map[layer_id]

    # ---------- API ----------
    # [FIX] Render Engine butuh method ini
    def get_frame(self, layer_id: str, time: float, props: dict = None) -> QImage:
        path = self._id_map.get(layer_id)
        if not path: return QImage()

        # 1. Raw Frame
        raw_frame = self._get_raw_frame(layer_id, path, time)
        if raw_frame is None: return QImage()

        # 2. Effects
        try:
            if props:
                processed_frame = self._apply_effects(raw_frame, props)
            else:
                processed_frame = raw_frame
        except Exception:
            processed_frame = raw_frame

        # 3. Convert
        return self._cv2_to_qimage(processed_frame)

    # Legacy support (jika ada komponen lama yang manggil ini)
    def get_frame_image(self, path: str, time: float) -> QImage:
        # Cari layer_id dari path (agak lambat tapi safe)
        found_id = None
        for lid, p in self._id_map.items():
            if p == path:
                found_id = lid
                break
        
        if found_id:
            return self.get_frame(found_id, time)
        return QImage() # Fail safe

    # ---------- INTERNAL ----------
    def _get_raw_frame(self, layer_id: str, path: str, time: float):
        if layer_id in self._image_cache:
            return self._image_cache[layer_id]

        cached = self._video_frame_cache.get(time)
        if cached is not None:
            return cached

        cap = self._get_reader(path)
        if not cap: return None

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_idx = int(time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, frame = cap.read()
        
        if ok:
            self._video_frame_cache.put(time, frame)
            return frame
        return None

    def _apply_effects(self, img, props: dict):
        img = img.copy() 
        c_props = props.get("color", {})
        fx_props = props.get("effect", {})

        bright = c_props.get("brightness", 0)
        contrast = c_props.get("contrast", 0)
        
        if bright != 0 or contrast != 0:
            alpha = 1.0 + (contrast / 100.0) 
            beta = bright
            img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

        sat = c_props.get("saturation", 0)
        hue = c_props.get("hue", 0)
        temp = c_props.get("temperature", 0)
        
        if sat != 0 or hue != 0 or temp != 0:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype("float32")
            (h, s, v) = cv2.split(hsv)

            if sat != 0:
                s = s * (1.0 + (sat / 100.0))
                s = np.clip(s, 0, 255)
            if hue != 0:
                h = h + hue
                h = np.mod(h, 180)

            hsv = cv2.merge([h, s, v])
            img = cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)

        if temp != 0:
            b, g, r = cv2.split(img)
            if temp > 0: # Warm
                r = cv2.add(r, int(temp))
                b = cv2.subtract(b, int(temp))
            else: # Cool
                r = cv2.subtract(r, int(abs(temp)))
                b = cv2.add(b, int(abs(temp)))
            img = cv2.merge([b, g, r])

        blur = fx_props.get("blur", 0)
        if blur > 0:
            k = int(blur) * 2 + 1 
            img = cv2.GaussianBlur(img, (k, k), 0)

        return img

    def _cv2_to_qimage(self, cv_img):
        if len(cv_img.shape) == 3:
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = cv_img.shape
        else:
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
            h, w, ch = cv_img.shape

        bytes_per_line = ch * w
        cv_img = np.ascontiguousarray(cv_img)
        qimg = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return qimg.copy()

    def _get_reader(self, path):
        if path not in self._readers:
            cap = cv2.VideoCapture(path)
            if cap.isOpened():
                self._readers[path] = cap
        return self._readers.get(path)

    def release_all(self):
        for r in self._readers.values(): r.release()
        self._readers.clear()
        self._image_cache.clear()
        self._video_frame_cache.clear()
    
    @staticmethod
    def _blank():
        pix = QPixmap(320, 180)
        pix.fill(QColor("#000000"))
        return pix