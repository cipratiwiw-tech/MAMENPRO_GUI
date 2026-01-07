from engine.layer_base import Layer
from effects.easing import EASING_MAP

class RotateAnimEffect(Layer):
    def __init__(self, start, end, from_angle, to_angle, easing="ease_out", enabled=True):
        super().__init__(z_index=0, enabled=enabled, name="RotateAnim")

        self.start = float(start)
        self.end = float(end)
        self.from_angle = float(from_angle)
        self.to_angle = float(to_angle)
        self.easing_fn = EASING_MAP.get(easing, EASING_MAP["linear"])

    def apply(self, frame, frame_index, fps, context):
        t = frame_index / fps

        if t < self.start:
            context["rotate"] = self.from_angle
            return frame

        if t > self.end:
            context["rotate"] = self.to_angle
            return frame

        p = (t - self.start) / (self.end - self.start)
        p = max(0.0, min(1.0, p))
        p = self.easing_fn(p)

        context["rotate"] = self.from_angle + (self.to_angle - self.from_angle) * p
        return frame
