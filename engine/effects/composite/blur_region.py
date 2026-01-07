import cv2
from engine.core.layer_base import Layer


class BlurRegionEffect(Layer):
    """
    Blur area tertentu pada video.
    Cocok untuk menutup subtitle / watermark video asli.
    """

    def __init__(
        self,
        x,
        y,
        width,
        height,
        blur_strength=25,
        start_frame=0,
        end_frame=None,
        z_index=0,
        enabled=True
    ):
        super().__init__(z_index=z_index, enabled=enabled, name="BlurRegion")

        self.x = int(x)
        self.y = int(y)
        self.w = int(width)
        self.h = int(height)

        if blur_strength % 2 == 0:
            blur_strength += 1
        self.blur_strength = blur_strength

        self.start_frame = start_frame
        self.end_frame = end_frame

    def apply(self, frame, frame_index, fps, context: dict):
        if frame_index < self.start_frame:
            return frame
        if self.end_frame is not None and frame_index > self.end_frame:
            return frame

        h, w = frame.shape[:2]

        x1 = max(0, self.x)
        y1 = max(0, self.y)
        x2 = min(w, self.x + self.w)
        y2 = min(h, self.y + self.h)

        if x2 <= x1 or y2 <= y1:
            return frame

        roi = frame[y1:y2, x1:x2]
        blurred = cv2.GaussianBlur(
            roi,
            (self.blur_strength, self.blur_strength),
            0
        )

        frame[y1:y2, x1:x2] = blurred
        return frame
