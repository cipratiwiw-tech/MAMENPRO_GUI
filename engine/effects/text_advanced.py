import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from engine.core.layer_base import Layer
from utils.paths import project_path
from effects.utils.easing import ease_value


class TextAdvancedEffect(Layer):
    def __init__(
        self,
        text,
        x,
        y,
        font_path,
        font_size=32,
        color=(255, 255, 255),
        opacity=1.0,
        z_index=0,
        enabled=True,
        align="left",
        stroke_width=0,
        stroke_color=(0, 0, 0),
    ):
        super().__init__(z_index=z_index, enabled=enabled, name="TextAdvanced")

        if not hasattr(self, "transform"):
            raise RuntimeError("LayerBase HARUS membuat self.transform sebelum TextAdvancedEffect")

        # Transform
        self.transform.x = int(x)
        self.transform.y = int(y)
        if self.transform.scale == 0:
            self.transform.scale = 1.0

        # Text props
        self.text = text
        self.font_path = font_path
        self.full_font_path = project_path(font_path)
        self.base_font_size = int(font_size)
        self.color = tuple(color)
        self.base_opacity = float(opacity)
        self.align = align
        self.stroke_width = int(stroke_width)
        self.stroke_color = tuple(stroke_color)
        self.padding = 10

        # Cache
        self._cached_surface = None
        self._cached_rotated = None
        self._cache_params = None
        self._last_rotation = None
        self._w_orig = 0
        self._h_orig = 0
        
        # Motion easing untuk drag
        self._target_x = x
        self._target_y = y
        self._easing_factor = 0.35  # Smoothing factor

    # -------------------------------------------------

    def _render_text_bitmap(self, scale):
        if not self.font_path or not os.path.exists(self.full_font_path):
            return None

        size = max(1, int(self.base_font_size * scale))

        try:
            font = ImageFont.truetype(self.full_font_path, size)
        except Exception:
            font = ImageFont.load_default()

        left, top, right, bottom = font.getbbox(self.text)
        text_w = right - left
        text_h = bottom - top

        pad = int(self.stroke_width * scale * 2) + self.padding
        img_w = int(text_w + pad * 2)
        img_h = int(text_h + pad * 2)

        img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        x_txt = pad - left
        y_txt = pad - top

        # Stroke
        if self.stroke_width > 0:
            sw = int(self.stroke_width * scale)
            for dx in range(-sw, sw + 1):
                for dy in range(-sw, sw + 1):
                    if dx * dx + dy * dy > sw * sw:
                        continue
                    draw.text((x_txt + dx, y_txt + dy), self.text, font=font, fill=self.stroke_color)

        # Fill
        draw.text((x_txt, y_txt), self.text, font=font, fill=self.color)

        self._w_orig = img_w
        self._h_orig = img_h

        return np.array(img)

    # -------------------------------------------------

    def apply(self, frame, frame_index, fps, context: dict):
        # === Adaptive color ===
        adaptive = context.get("adaptive_text", {}).get("color")
        if adaptive is not None and adaptive != self.color:
            self.color = adaptive
            self._cached_surface = None

        scale = self.transform.scale
        rot = getattr(self.transform, "rotation", 0)

        cache_key = (
            self.text,
            self.font_path,
            self.color,
            self.stroke_width,
            self.stroke_color,
            round(scale, 3),
        )

        # Render bitmap
        if self._cached_surface is None or self._cache_params != cache_key:
            surf = self._render_text_bitmap(scale)
            if surf is None:
                return frame
            self._cached_surface = surf
            self._cache_params = cache_key
            self._cached_rotated = None
            self._last_rotation = None

        # Rotate cache
        if self._cached_rotated is None or self._last_rotation != rot:
            if rot == 0:
                self._cached_rotated = self._cached_surface
            else:
                pil = Image.fromarray(self._cached_surface)
                pil = pil.rotate(rot, expand=True, resample=Image.BICUBIC)
                self._cached_rotated = np.array(pil)
            self._last_rotation = rot

        overlay = self._cached_rotated
        if overlay is None:
            return frame

        h, w = overlay.shape[:2]

        cx = self.transform.x + self._w_orig / 2
        cy = self.transform.y + self._h_orig / 2
        px = int(cx - w / 2)
        py = int(cy - h / 2)

        fh, fw = frame.shape[:2]
        x1, y1 = max(0, px), max(0, py)
        x2, y2 = min(fw, px + w), min(fh, py + h)

        if x1 >= x2 or y1 >= y2:
            return frame

        ox1, oy1 = x1 - px, y1 - py
        ox2, oy2 = ox1 + (x2 - x1), oy1 + (y2 - y1)

        roi = frame[y1:y2, x1:x2]
        ov = overlay[oy1:oy2, ox1:ox2]

        alpha = ov[:, :, 3:4].astype(np.float32) / 255.0
        alpha *= self.base_opacity
        alpha *= float(context.get("opacity", 1.0))
        alpha = np.clip(alpha, 0.0, 1.0)

        rgb = ov[:, :, :3].astype(np.float32)
        bg = roi.astype(np.float32)

        roi[:] = (alpha * rgb + (1.0 - alpha) * bg).astype(np.uint8)
        return frame

    # -------------------------------------------------

    def get_bbox(self):
        if self._cached_surface is None:
            self._render_text_bitmap(self.transform.scale)

        w = self._w_orig + self.padding * 2
        h = self._h_orig + self.padding * 2

        return (
            int(self.transform.x - self.padding),
            int(self.transform.y - self.padding),
            int(w),
            int(h),
        )

    # di TextAdvancedEffect

    def set_drag_target(self, target_x, target_y):
        """Set target position untuk easing saat drag."""
        self._target_x = float(target_x)
        self._target_y = float(target_y)
    
    def set_easing_factor(self, factor):
        """Set faktor smoothing (0.1-0.9), lebih rendah = lebih smooth."""
        self._easing_factor = max(0.01, min(0.99, float(factor)))
    
    def update_with_easing(self):
        """Update posisi dengan motion easing exponential."""
        self.transform.x += (self._target_x - self.transform.x) * self._easing_factor
        self.transform.y += (self._target_y - self.transform.y) * self._easing_factor

    def draw_fast(self, frame):
        """
        Super-fast preview draw dengan alpha mask (TANPA alpha blend float).
        Aman, HALUS, TANPA background hitam.
        Includes motion easing untuk smooth drag.
        """
        if self._cached_surface is None:
            self._render_text_bitmap(self.transform.scale)

        if self._cached_surface is None:
            return frame

        # Update posisi dengan easing
        self.update_with_easing()

        overlay = self._cached_surface
        h, w = overlay.shape[:2]

        fh, fw = frame.shape[:2]
        x = int(self.transform.x)
        y = int(self.transform.y)
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(fw, x + w)
        y2 = min(fh, y + h)

        if x1 >= x2 or y1 >= y2:
            return frame

        ox1 = x1 - x
        oy1 = y1 - y
        ox2 = ox1 + (x2 - x1)
        oy2 = oy1 + (y2 - y1)

        ov = overlay[oy1:oy2, ox1:ox2]
        rgb = ov[..., :3]
        alpha = ov[..., 3]

        mask = alpha > 0

        roi = frame[y1:y2, x1:x2]
        roi[mask] = rgb[mask]

        return frame
