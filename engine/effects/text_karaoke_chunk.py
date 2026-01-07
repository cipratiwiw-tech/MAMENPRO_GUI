import numpy as np
from PIL import Image, ImageDraw, ImageFont
from engine.core.layer_base import Layer
from utils.paths import project_path


class KaraokeChunkTimestampEffect(Layer):
    """
    Karaoke subtitle CHUNK MODE (non-overlapping).
    Menampilkan N kata sekaligus, lalu lompat ke chunk berikutnya.
    """

    def __init__(
        self,
        words,
        x,
        y,
        chunk_size=3,
        anchor="center",
        font_path="assets/fonts/Montserrat-Bold.ttf",
        font_size=42,
        base_color=(200, 200, 200),
        active_color=(0, 0, 0),
        highlight_color=(255, 215, 0),
        padding_x=10,
        padding_y=6,
        radius=8,
        z_index=0,
        enabled=True
    ):
        super().__init__(z_index=z_index, enabled=enabled, name="KaraokeChunk")

        self.words_data = words
        self.x = x
        self.y = y
        self.chunk_size = int(chunk_size)
        self.anchor = anchor

        self.font_path = project_path(font_path)
        self.font_size = font_size
        self._font = ImageFont.truetype(self.font_path, font_size)

        self.base_color = base_color
        self.active_color = active_color
        self.highlight_color = highlight_color

        self.padding_x = int(padding_x)
        self.padding_y = int(padding_y)
        self.radius = int(radius)

        # Precompute chunk ranges
        self.chunks = []
        for i in range(0, len(words), self.chunk_size):
            chunk = words[i:i + self.chunk_size]
            self.chunks.append({
                "start": chunk[0]["start"],
                "end": chunk[-1]["end"],
                "words": [w["word"] for w in chunk]
            })

    # --------------------------------------------------

    def apply(self, frame, frame_index, fps, context):
        t = frame_index / fps

        active_chunk = None
        for ch in self.chunks:
            if ch["start"] <= t <= ch["end"]:
                active_chunk = ch
                break

        if active_chunk is None:
            return frame

        opacity = int(255 * float(context.get("opacity", 1.0)))

        h, w = frame.shape[:2]
        px = self._resolve(self.x, w)
        py = self._resolve(self.y, h)

        base = Image.fromarray(frame).convert("RGBA")
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        words = active_chunk["words"]
        widths = [draw.textbbox((0, 0), w, font=self._font)[2] for w in words]
        space_w = draw.textbbox((0, 0), " ", font=self._font)[2]
        line_w = sum(widths) + space_w * (len(widths) - 1)

        bbox = draw.textbbox((0, 0), "Hg", font=self._font)
        line_h = bbox[3] - bbox[1]

        x = px - line_w // 2 if self.anchor == "center" else px
        y = py

        cx = x
        for i, word in enumerate(words):
            bw = widths[i]

            draw.rounded_rectangle(
                [
                    cx - self.padding_x,
                    y - self.padding_y,
                    cx + bw + self.padding_x,
                    y + line_h + self.padding_y
                ],
                radius=self.radius,
                fill=self.highlight_color + (opacity,)
            )

            draw.text(
                (cx, y),
                word,
                font=self._font,
                fill=self.active_color + (opacity,)
            )

            cx += bw + space_w

        out = Image.alpha_composite(base, layer)
        return np.array(out.convert("RGB"))

    # --------------------------------------------------

    def _resolve(self, value, max_value):
        if isinstance(value, str) and value.endswith("%"):
            return int(float(value[:-1]) / 100 * max_value)
        return int(value)
