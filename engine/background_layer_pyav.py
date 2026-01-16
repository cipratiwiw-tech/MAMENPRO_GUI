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
        
        # [UPDATE] Parameter Vignette & Blur
        self.blur = 0   
        self.vig_strength = 0.0
        self.vig_radius = 0.85
        self.vig_angle = 0.0

        self._frame_cache = {}

    # =====================
    # SOURCE
    # =====================
    def set_source(self, path: str):
        self.path = path
        self._close()

        try:
            self.container = av.open(path)
            self.stream = self.container.streams.video[0]
            self.stream.thread_type = "AUTO"
        except Exception as e:
            print(f"Error opening background: {e}")
            self.container = None
            self.stream = None

        self._frame_cache.clear()

    def set_enabled(self, value: bool):
        self.enabled = value

    def update_state(self, data: dict):
        self.x = data.get("x", self.x)
        self.y = data.get("y", self.y)
        self.scale = data.get("scale", self.scale)
        self.blur = data.get("blur", self.blur)
        
        # [UPDATE] Ambil data vignette yang lengkap
        self.vig_strength = data.get("vig_strength", self.vig_strength)
        self.vig_radius = data.get("vig_radius", self.vig_radius)
        self.vig_angle = data.get("vig_angle", self.vig_angle)

    # =====================
    # RENDER
    # =====================
    def render(self, canvas: np.ndarray, frame_idx: int, fps: float):
        if not self.enabled or not self.container:
            return canvas

        frame = self._get_frame(frame_idx)
        if frame is None:
            return canvas

        # 1. Scale
        frame = self._apply_scale(frame)
        
        # 2. Blur
        if self.blur > 0:
            k = int(self.blur * 2 + 1)
            frame = cv2.GaussianBlur(frame, (k, k), 0)

        # 3. Vignette (New Formula)
        if self.vig_strength > 0:
            frame = self._apply_vignette(frame)
            
        # 4. Color Matching (RGB -> RGBA if needed)
        if canvas.shape[2] == 4 and frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2RGBA)

        # 5. Composite
        canvas = self._composite(canvas, frame)
        return canvas

    # =====================
    # INTERNAL LOGIC
    # =====================
    def _apply_vignette(self, img: np.ndarray):
        """
        Menerapkan rumus vignette 'Center Baseline' menggunakan Numpy Vectorization.
        Rumus:
          aspect = w / h
          nx = (x / w - 0.5) * aspect
          ny = (y / h - 0.5)
          dist = sqrt(nx*nx + ny*ny)
          ... angle rotation ...
          v = smoothstep(vig_rad, vig_rad - 0.4, dist)
          out = color * (1 - (1-v) * str)  <-- Logic adjusted for darkening edges
        """
        h, w = img.shape[:2]
        if h == 0 or w == 0: return img

        # 1. Buat Coordinate Grid (Vectorized)
        y_idx, x_idx = np.indices((h, w))
        
        # 2. Hitung Aspect Ratio & Normalized Coordinates
        aspect = w / h
        nx = (x_idx / w - 0.5) * aspect
        ny = (y_idx / h - 0.5)
        
        # 3. Hitung Jarak Dasar
        dist = np.sqrt(nx**2 + ny**2)

        # 4. Masukkan Logika Angle (Rotation Offset)
        # rad = vig_ang * PI / 180
        # dist += (nx*cos(rad) + ny*sin(rad)) * 0.3
        if self.vig_angle != 0:
            rad = np.radians(self.vig_angle)
            dist += (nx * np.cos(rad) + ny * np.sin(rad)) * 0.3

        # 5. Smoothstep (Custom Implementation for Numpy)
        # v = smoothstep(vig_rad, vig_rad - 0.4, dist)
        # edge0 = vig_rad (outer), edge1 = vig_rad - 0.4 (inner)
        edge0 = self.vig_radius
        edge1 = self.vig_radius - 0.4
        
        # Clamp value for smoothstep: (x - edge0) / (edge1 - edge0)
        # Karena edge1 < edge0, pembaginya negatif, membalikkan logika (jauh=0, dekat=1)
        denom = edge1 - edge0
        if abs(denom) < 1e-6: denom = -0.4 # Safety division

        t = np.clip((dist - edge0) / denom, 0.0, 1.0)
        v = t * t * (3.0 - 2.0 * t) # Hermite interpolation (Smoothstep standard)

        # v = 1.0 di center (terang)
        # v = 0.0 di pojok (gelap)

        # 6. Apply to Image
        # Kita ingin menggelapkan area di mana v mendekati 0.
        # Masking factor = 1 - (1 - v) * Strength
        # Contoh: Strength 1.0, v=0 (pojok) -> Factor = 0 (Hitam)
        #         Strength 0.5, v=0 (pojok) -> Factor = 0.5 (Setengah gelap)
        mask = 1.0 - (1.0 - v) * self.vig_strength
        
        # Expand mask to 3 channels (H, W, 1) -> (H, W, 3)
        mask = mask[..., np.newaxis]
        
        # Kalikan
        img_float = img.astype(np.float32)
        img_out = img_float * mask
        
        return np.clip(img_out, 0, 255).astype(np.uint8)

    def _get_frame(self, frame_idx: int):
        if frame_idx in self._frame_cache:
            return self._frame_cache[frame_idx].copy()

        try:
            target_ts = int(frame_idx / self.stream.average_rate)
            # Optimization: Only seek if diff is large to avoid stutter
            self.container.seek(target_ts)
        except Exception:
            pass

        try:
            for frame in self.container.decode(self.stream):
                img = frame.to_ndarray(format="rgb24")
                self._frame_cache[frame_idx] = img
                return img
        except StopIteration:
            pass # End of stream
            
        return None

    def _apply_scale(self, img: np.ndarray):
        if self.scale == 100:
            return img

        h, w = img.shape[:2]
        s = self.scale / 100.0
        nw = max(1, int(w * s))
        nh = max(1, int(h * s))

        # Gunakan resize cv2 karena lebih cepat daripada av.reformat untuk real-time
        return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)

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
        
        # Handle alpha channel blending if frame became RGBA due to color match
        if frame.shape[2] == 4 and canvas.shape[2] == 4:
            alpha_s = frame[fy1:fy2, fx1:fx2, 3] / 255.0
            alpha_l = 1.0 - alpha_s
            
            for c in range(3):
                canvas[y1:y2, x1:x2, c] = (alpha_s * frame[fy1:fy2, fx1:fx2, c] +
                                           alpha_l * canvas[y1:y2, x1:x2, c])
            # Update canvas alpha (simple max)
            canvas[y1:y2, x1:x2, 3] = np.maximum(canvas[y1:y2, x1:x2, 3], frame[fy1:fy2, fx1:fx2, 3])
        else:
            # Direct copy for opaque background
            canvas[y1:y2, x1:x2] = frame[fy1:fy2, fx1:fx2]
            
        return canvas

    def _close(self):
        if self.container:
            self.container.close()
        self.container = None
        self.stream = None