from effects.easing import EASING_MAP

class ScaleEffect:
    def __init__(self, from_scale, to_scale, start, end, easing="linear"):
        self.from_scale = float(from_scale)
        self.to_scale = float(to_scale)
        self.start = float(start)
        self.end = float(end)
        self.easing = EASING_MAP.get(easing, EASING_MAP["linear"])

    def apply(self, frame, frame_index, fps, context):
        t = frame_index / fps

        # ⛔ DI LUAR WINDOW → JANGAN SENTUH CONTEXT
        if t < self.start or t > self.end:
            return frame

        # hitung progress
        p = (t - self.start) / (self.end - self.start)
        p = max(0.0, min(1.0, p))
        p = self.easing(p)

        scale = self.from_scale + (self.to_scale - self.from_scale) * p

        # tulis hanya saat aktif
        context["scale"] = max(0.01, scale)
        return frame
