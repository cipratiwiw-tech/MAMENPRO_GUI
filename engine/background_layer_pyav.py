import av
import numpy as np
import cv2


class BackgroundLayer:
    def __init__(self):
        self.enabled = True
        self.path = None
        self.container = None
        self.stream = None

        self.x = 0
        self.y = 0
        self.scale = 100
        self.blur = 0   # placeholder (opsional)
        self.vig = 0    # placeholder (opsional)

        self._frame_cache = {}

    # =====================
    # SOURCE
    # =====================
    def set_source(self, path: str):
        self.path = path
        self._close()

        self.container = av.open(path)
        self.stream = self.container.streams.video[0]
        self.stream.thread_type = "AUTO"

        self._frame_cache.clear()

    def set_enabled(self, value: bool):
        self.enabled = value

    def update_state(self, data: dict):
        self.x = data.get("x", self.x)
        self.y = data.get("y", self.y)
        self.scale = data.get("scale", self.scale)
        self.blur = data.get("blur", self.blur)
        self.vig = data.get("vig", self.vig)

    # =====================
    # RENDER
    # =====================
    def render(self, canvas: np.ndarray, frame_idx: int, fps: float):
        if not self.enabled or not self.container:
            return canvas

        frame = self._get_frame(frame_idx)
        if frame is None:
            return canvas

        frame = self._apply_scale(frame)
        
        # FIX: Apply Blur 
        if hasattr(self, 'blur') and self.blur > 0:
            k = int(self.blur * 2 + 1)
            frame = cv2.GaussianBlur(frame, (k, k), 0)
            
        # FIX: Matching Channels (RGBA/RGB) [cite: 23]
        if canvas.shape[2] == 4 and frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2RGBA)

        canvas = self._composite(canvas, frame)
        return canvas

        frame = self._get_frame(frame_idx)
        if frame is None:
            return canvas

        frame = self._apply_scale(frame)
        canvas = self._composite(canvas, frame)

        return canvas

    # =====================
    # INTERNAL
    # =====================
    def _get_frame(self, frame_idx: int):
        if frame_idx in self._frame_cache:
            return self._frame_cache[frame_idx].copy()

        try:
            self.container.seek(int(frame_idx / self.stream.average_rate))
        except Exception:
            pass

        for frame in self.container.decode(self.stream):
            img = frame.to_ndarray(format="rgb24")
            self._frame_cache[frame_idx] = img
            return img

        return None

    def _apply_scale(self, img: np.ndarray):
        if self.scale == 100:
            return img

        h, w = img.shape[:2]
        s = self.scale / 100.0
        nw = int(w * s)
        nh = int(h * s)

        return np.array(
            av.VideoFrame.from_ndarray(img, format="rgb24")
            .reformat(width=nw, height=nh)
            .to_ndarray()
        )

    def _composite(self, canvas, frame):
        ch, cw = canvas.shape[:2]
        fh, fw = frame.shape[:2]

        x = int(self.x)
        y = int(self.y)

        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(cw, x + fw)
        y2 = min(ch, y + fh)

        if x1 >= x2 or y1 >= y2:
            return canvas

        fx1 = x1 - x
        fy1 = y1 - y
        fx2 = fx1 + (x2 - x1)
        fy2 = fy1 + (y2 - y1)

        canvas[y1:y2, x1:x2] = frame[fy1:fy2, fx1:fx2]
        return canvas

    def _close(self):
        if self.container:
            self.container.close()
        self.container = None
        self.stream = None
