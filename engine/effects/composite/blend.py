from engine.core.layer_base import Layer
from utils.blend_modes import BLEND_MODES


class BlendEffect(Layer):
    def __init__(self, mode="normal", opacity=1.0, start=0.0, end=None):
        super().__init__(z_index=0, enabled=True, name="Blend")
        self.mode = mode
        self.opacity = float(opacity)
        self.start = float(start)
        self.end = float(end) if end is not None else None

    def apply(self, frame, frame_index, fps, context: dict):
        t = frame_index / fps

        if t < self.start:
            return frame
        if self.end is not None and t > self.end:
            return frame

        base_frame = context.get("base_frame", frame)


        blend_func = BLEND_MODES.get(self.mode)
        if blend_func is None:
            return frame

        global_opacity = float(context.get("opacity", 1.0))
        final_opacity = max(0.0, min(1.0, self.opacity * global_opacity))

        try:
            return blend_func(base_frame, frame, final_opacity)
        except Exception:
            return frame
