import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from effects.easing import ease_out_back


class KaraokeBounceScaleEffect:
    """
    Karaoke subtitle dengan bounce + scale pada kata aktif.
    Cocok dikombinasikan dengan highlight / gradient.
    """

    def __init__(
        self,
        text,
        x,
        y,
        start,
        end,
        max_width,
        anchor="center",
        line_spacing=10,

        font_path="assets/fonts/Montserrat-Bold.ttf",
        font_size=40,

        base_color=(200, 200, 200),
        active_color=(255, 255, 255),

        scale_from=1.0,
        scale_to=1.25,
        bounce_strength=0.35,   # semakin besar → makin pop

        z_index=0
    ):
        self.text = text
        self.words = text.split(" ")

        self.x = x
        self.y = y
        self.start = float(start)
        self.end = float(end)
        self.max_width = max_width
        self.anchor = anchor
        self.line_spacing = int(line_spacing)

        self.font_path = font_path
        self.font_size = font_size

        self.base_color = base_color
        self.active_color = active_color

        self.scale_from = float(scale_from)
        self.scale_to = float(scale_to)
        self.bounce_strength = float(bounce_strength)

        self.z_index = z_index

        self._font_base = ImageFont.truetype(font_path, font_size)
        self._lines = None

    # --------------------------------------------------

    def _compute_lines(self, draw, max_w):
        space_w = draw.textbbox((0, 0), " ", font=self._font_base)[2]
        lines = []
        cur_words = []
        cur_w = 0

        for word in self.words:
            bw = draw.textbbox((0, 0), word, font=self._font_base)[2]
            next_w = bw if not cur_words else cur_w + space_w + bw

            if next_w <= max_w:
                cur_words.append(word)
                cur_w = next_w
            else:
                lines.append(cur_words)
                cur_words = [word]
                cur_w = bw

        if cur_words:
            lines.append(cur_words)

        return lines

    # --------------------------------------------------

    def apply(self, frame, frame_index, fps, context):
        t = frame_index / fps
        if t < self.start:
            return frame

        p = (t - self.start) / (self.end - self.start)
        p = max(0.0, min(1.0, p))

        total_words = len(self.words)
        if total_words == 0:
            return frame

        active_word = min(total_words - 1, int(p * total_words))

        h, w = frame.shape[:2]
        px = self._resolve(self.x, w)
        py = self._resolve(self.y, h)

        base = Image.fromarray(frame).convert("RGBA")
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        # resolve max width
        if isinstance(self.max_width, str) and self.max_width.endswith("%"):
            max_w = int(float(self.max_width[:-1]) / 100 * w)
        else:
            max_w = int(self.max_width)

        # precompute wrap
        if self._lines is None:
            self._lines = self._compute_lines(draw, max_w)

        # metrics
        bbox = draw.textbbox((0, 0), "Hg", font=self._font_base)
        line_h = bbox[3] - bbox[1]
        total_h = len(self._lines) * line_h + (len(self._lines) - 1) * self.line_spacing

        start_y = py - total_h // 2 if self.anchor == "center" else py

        word_idx = 0
        y = start_y

        for line_words in self._lines:
            widths = [draw.textbbox((0, 0), w, font=self._font_base)[2] for w in line_words]
            space_w = draw.textbbox((0, 0), " ", font=self._font_base)[2]
            line_w = sum(widths) + space_w * (len(widths) - 1)

            x = px - line_w // 2 if self.anchor == "center" else px
            cx = x

            for i, word in enumerate(line_words):
                is_active = (word_idx == active_word)

                # scale bounce
                if is_active:
                    bounce_p = ease_out_back(1.0)
                    scale = self.scale_from + (self.scale_to - self.scale_from) * bounce_p
                    font = ImageFont.truetype(
                        self.font_path,
                        int(self.font_size * scale)
                    )
                    color = self.active_color
                else:
                    font = self._font_base
                    color = self.base_color

                draw.text(
                    (cx, y),
                    word,
                    font=font,
                    fill=color + (255,)
                )

                bw = draw.textbbox((0, 0), word, font=font)[2]
                cx += bw + space_w
                word_idx += 1

            y += line_h + self.line_spacing

        out = Image.alpha_composite(base, layer)
        return np.array(out.convert("RGB"))

    # --------------------------------------------------

    def _resolve(self, value, max_value):
        if isinstance(value, str) and value.endswith("%"):
            return int(float(value[:-1]) / 100 * max_value)
        return int(value)
