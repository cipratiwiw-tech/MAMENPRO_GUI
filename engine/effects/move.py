from engine.layer_base import Layer
from effects.easing import EASING_MAP

class MoveEffect(Layer):
    def __init__(self, from_x, from_y, to_x, to_y, start, end, easing="linear", enabled=True):
        super().__init__(z_index=0, enabled=enabled, name="MoveEffect")

        self.fx = float(from_x); self.fy = float(from_y)
        self.tx = float(to_x);   self.ty = float(to_y)
        self.start = float(start); self.end = float(end)
        self.easing = EASING_MAP.get(easing, EASING_MAP["linear"])

    def apply(self, frame, frame_index, fps, context):
        t = frame_index / fps

        if t <= self.start:
            p = 0.0
        elif t >= self.end:
            p = 1.0
        else:
            p = (t - self.start) / (self.end - self.start)

        p = self.easing(p)

        context["x"] = int(self.fx + (self.tx - self.fx) * p)
        context["y"] = int(self.fy + (self.ty - self.fy) * p)

        return frame
