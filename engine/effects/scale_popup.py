from effects.easing import EASING_MAP

class ScalePopupEffect:
    def __init__(
        self,
        start,
        end,
        from_scale=0.05,
        to_scale=1.0,
        easing="ease_out_back"
    ):
        self.start = float(start)
        self.end = float(end)
        self.from_scale = float(from_scale)
        self.to_scale = float(to_scale)
        self.easing_fn = EASING_MAP.get(easing, EASING_MAP["linear"])

    def apply(self, frame, frame_index, fps, context):
        t = frame_index / fps

        if t < self.start:
            context["scale"] = self.from_scale
            return frame

        if t > self.end:
            context["scale"] = self.to_scale
            return frame

        # progress linear
        p = (t - self.start) / (self.end - self.start)
        p = max(0.0, min(1.0, p))

        # ✨ easing applied here
        p = self.easing_fn(p)

        scale = self.from_scale + (self.to_scale - self.from_scale) * p
        context["scale"] = scale
        return frame
