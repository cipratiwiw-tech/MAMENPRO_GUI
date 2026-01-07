import cv2
import numpy as np
from engine.core.layer_base import Layer


class ImageMaskEffect(Layer):
    """
    Image-based mask (grayscale / alpha).
    Putih = terlihat, hitam = transparan.
    """

    def __init__(
        self,
        mask_path,
        x="50%",
        y="50%",
        scale=1.0,
        feather=0,
        invert=False,
        z_index=-50,
        enabled=True,
    ):
        super().__init__(z_index=z_index, enabled=enabled, name="ImageMask")

        self.mask_path = mask_path
        self.x = x
        self.y = y
        self.scale = float(scale)
        self.feather = int(feather)
        self.invert = invert

        self._mask_img = None

    # --------------------------------------------------

    def apply(self, frame, frame_index, fps, context):
        if self._mask_img is None:
            self._mask_img = cv2.imread(self.mask_path, cv2.IMREAD_GRAYSCALE)
            if self._mask_img is None:
                return frame

        h, w = frame.shape[:2]
        cx = self._resolve(self.x, w)
        cy = self._resolve(self.y, h)

        mask = self._mask_img.copy()

        if self.scale != 1.0:
            mask = cv2.resize(
                mask,
                None,
                fx=self.scale,
                fy=self.scale,
                interpolation=cv2.INTER_LINEAR
            )

        mh, mw = mask.shape[:2]

        canvas = np.zeros((h, w), dtype=np.uint8)
        x0 = cx - mw // 2
        y0 = cy - mh // 2
        x1 = x0 + mw
        y1 = y0 + mh

        sx0 = max(0, -x0)
        sy0 = max(0, -y0)
        sx1 = mw - max(0, x1 - w)
        sy1 = mh - max(0, y1 - h)

        tx0 = max(0, x0)
        ty0 = max(0, y0)
        tx1 = tx0 + (sx1 - sx0)
        ty1 = ty0 + (sy1 - sy0)

        canvas[ty0:ty1, tx0:tx1] = mask[sy0:sy1, sx0:sx1]

        if self.feather > 0:
            k = self.feather * 2 + 1
            canvas = cv2.GaussianBlur(canvas, (k, k), 0)

        if self.invert:
            canvas = 255 - canvas

        if frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
            context["force_bgra"] = True

        alpha = frame[:, :, 3].astype(np.float32)
        mask_f = canvas.astype(np.float32) / 255.0
        opacity = float(context.get("opacity", 1.0))
        frame[:, :, 3] = (alpha * mask_f * opacity).astype(np.uint8)


        return frame

    def _resolve(self, value, max_value):
        if isinstance(value, str) and value.endswith("%"):
            return int(float(value[:-1]) / 100 * max_value)
        return int(value)
