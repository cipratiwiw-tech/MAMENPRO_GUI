import cv2
import numpy as np
from engine.core.layer_base import Layer


class ImageOverlayEffect(Layer):
    def __init__(self, x=0, y=0, scale=1.0, z_index=0, enabled=True):
        super().__init__(z_index=z_index, enabled=enabled, name="ImageOverlay")
        self.x = int(x)
        self.y = int(y)
        self.scale = float(scale)

    def apply(self, frame, frame_index, fps, context):
        overlay = context.get("overlay_frame")
        if overlay is None:
            return frame

        if overlay.ndim != 3 or overlay.shape[2] not in (3, 4):
            return frame

        h_bg, w_bg = frame.shape[:2]

        if self.scale != 1.0:
            overlay = cv2.resize(
                overlay, None,
                fx=self.scale, fy=self.scale,
                interpolation=cv2.INTER_LINEAR
            )

        h_ov, w_ov = overlay.shape[:2]

        x1 = max(self.x, 0)
        y1 = max(self.y, 0)
        x2 = min(self.x + w_ov, w_bg)
        y2 = min(self.y + h_ov, h_bg)

        if x1 >= x2 or y1 >= y2:
            return frame

        ov_x1 = x1 - self.x
        ov_y1 = y1 - self.y
        ov_x2 = ov_x1 + (x2 - x1)
        ov_y2 = ov_y1 + (y2 - y1)

        roi_bg = frame[y1:y2, x1:x2]
        roi_ov = overlay[ov_y1:ov_y2, ov_x1:ov_x2]

        if roi_ov.shape[2] == 4:
            alpha = roi_ov[:, :, 3:4].astype(np.float32) / 255.0
            alpha *= float(context.get("opacity", 1.0))
            alpha = np.clip(alpha, 0.0, 1.0)

            rgb = roi_ov[:, :, :3].astype(np.float32)
            bg = roi_bg.astype(np.float32)

            blended = alpha * rgb + (1.0 - alpha) * bg
            frame[y1:y2, x1:x2] = blended.astype(np.uint8)
        else:
            frame[y1:y2, x1:x2] = roi_ov

        # prevent overlay carry-over
        context["overlay_frame"] = None
        return frame

