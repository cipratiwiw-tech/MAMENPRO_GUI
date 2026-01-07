import cv2
import numpy as np
from engine.core.layer_base import Layer


class BlurFeatherRoundedEffect(Layer):
    """
    Blur area dengan feather + rounded corner.
    """

    def __init__(
        self,
        x,
        y,
        width,
        height,
        blur_strength=31,
        corner_radius=30,
        feather=20,
        start_frame=0,
        end_frame=None,
        z_index=0,
        enabled=True
    ):
        super().__init__(z_index=z_index, enabled=enabled, name="BlurFeatherRounded")

        self.x = int(x)
        self.y = int(y)
        self.w = int(width)
        self.h = int(height)

        if blur_strength % 2 == 0:
            blur_strength += 1
        self.blur_strength = blur_strength

        self.corner_radius = int(corner_radius)
        self.feather = int(feather)

        self.start_frame = start_frame
        self.end_frame = end_frame

    def _rounded_rect_mask(self, shape):
        mask = np.zeros(shape[:2], dtype=np.uint8)

        x1, y1 = self.x, self.y
        x2, y2 = self.x + self.w, self.y + self.h
        r = min(self.corner_radius, self.w // 2, self.h // 2)

        cv2.rectangle(mask, (x1 + r, y1), (x2 - r, y2), 255, -1)
        cv2.rectangle(mask, (x1, y1 + r), (x2, y2 - r), 255, -1)

        cv2.circle(mask, (x1 + r, y1 + r), r, 255, -1)
        cv2.circle(mask, (x2 - r, y1 + r), r, 255, -1)
        cv2.circle(mask, (x1 + r, y2 - r), r, 255, -1)
        cv2.circle(mask, (x2 - r, y2 - r), r, 255, -1)

        return mask

    def apply(self, frame, frame_index, fps, context: dict):
        if frame_index < self.start_frame:
            return frame
        if self.end_frame is not None and frame_index > self.end_frame:
            return frame

        blurred = cv2.GaussianBlur(
            frame,
            (self.blur_strength, self.blur_strength),
            0
        )

        mask = self._rounded_rect_mask(frame.shape)

        if self.feather > 0:
            k = self.feather * 2 + 1
            mask = cv2.GaussianBlur(mask, (k, k), 0)

        alpha = mask.astype(float) / 255.0
        alpha = cv2.merge([alpha, alpha, alpha])

        out = frame * (1 - alpha) + blurred * alpha
        return out.astype(np.uint8)
