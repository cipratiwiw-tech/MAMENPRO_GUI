import cv2
import numpy as np
from engine.core.layer_base import Layer


class ShapeMaskEffect(Layer):
    def __init__(
        self,
        shape="rect",
        x="50%",
        y="50%",
        width=400,
        height=300,
        radius=40,
        feather=0,
        invert=False,
        enabled=True,
        z_index=-50
    ):
        super().__init__(z_index=z_index, enabled=enabled, name="ShapeMask")
        self.shape = shape
        self.x = x
        self.y = y
        self.width = int(width)
        self.height = int(height)
        self.radius = int(radius)
        self.feather = int(feather)
        self.invert = invert

    def apply(self, frame, frame_index, fps, context):
        opacity = float(context.get("opacity", 1.0))
        opacity = max(0.0, min(1.0, opacity))

        if opacity <= 0:
            return frame

        if frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)

        h, w = frame.shape[:2]
        cx = self._resolve(self.x, w)
        cy = self._resolve(self.y, h)

        mask = np.zeros((h, w), dtype=np.uint8)

        if self.shape == "rect":
            x0 = cx - self.width // 2
            y0 = cy - self.height // 2
            x1 = cx + self.width // 2
            y1 = cy + self.height // 2
            cv2.rectangle(mask, (x0, y0), (x1, y1), 255, -1)

        elif self.shape == "round_rect":
            self._draw_round_rect(mask, cx, cy)

        elif self.shape == "circle":
            r = min(self.width, self.height) // 2
            cv2.circle(mask, (cx, cy), r, 255, -1)

        if self.feather > 0:
            k = self.feather * 2 + 1
            mask = cv2.GaussianBlur(mask, (k, k), 0)

        if self.invert:
            mask = 255 - mask

        alpha = frame[:, :, 3].astype(np.float32)
        mask_f = (mask.astype(np.float32) / 255.0) * opacity
        frame[:, :, 3] = np.clip(alpha * mask_f, 0, 255).astype(np.uint8)

        return frame

    def _draw_round_rect(self, mask, cx, cy):
        w, h = self.width, self.height
        r = min(self.radius, w // 2, h // 2)

        x0 = cx - w // 2
        y0 = cy - h // 2
        x1 = cx + w // 2
        y1 = cy + h // 2

        cv2.rectangle(mask, (x0 + r, y0), (x1 - r, y1), 255, -1)
        cv2.rectangle(mask, (x0, y0 + r), (x1, y1 - r), 255, -1)

        cv2.circle(mask, (x0 + r, y0 + r), r, 255, -1)
        cv2.circle(mask, (x1 - r, y0 + r), r, 255, -1)
        cv2.circle(mask, (x0 + r, y1 - r), r, 255, -1)
        cv2.circle(mask, (x1 - r, y1 - r), r, 255, -1)

    def _resolve(self, value, max_value):
        if isinstance(value, str) and value.endswith("%"):
            return int(float(value[:-1]) / 100 * max_value)
        return int(value)
