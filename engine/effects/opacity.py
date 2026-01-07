from effects.utils.easing import EASING_MAP
from engine.core.layer_base import Layer


class OpacityEffect(Layer):
    def __init__(self, start, end, from_value=0.0, to_value=1.0, easing="linear"):
        super().__init__(z_index=0, enabled=True, name="Opacity")
        self.start = float(start)
        self.end = float(end)
        self.from_value = float(from_value)
        self.to_value = float(to_value)
        self.easing_fn = EASING_MAP.get(easing, EASING_MAP["linear"])

    def apply(self, frame, frame_index, fps, context: dict):
        t = frame_index / fps

        if self.end <= self.start:
            context["opacity"] = self.to_value
            return frame

        if t <= self.start:
            context["opacity"] = self.from_value
            return frame

        if t >= self.end:
            context["opacity"] = self.to_value
            return frame

        p = (t - self.start) / (self.end - self.start)
        p = max(0.0, min(1.0, self.easing_fn(p)))

        opacity = self.from_value + (self.to_value - self.from_value) * p
        context["opacity"] = max(0.0, min(1.0, opacity))
        return frame
