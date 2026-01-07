from engine.core.layer_base import Layer
from effects.composite.chroma.despill_math import despill_rgba


class DespillEffect(Layer):
    def __init__(self, strength=0.5, z_index=0, enabled=True):
        super().__init__(z_index=z_index, enabled=enabled, name="Despill")
        self.strength = strength

    def apply(self, frame, frame_index, fps, context):
        if frame.shape[2] != 4:
            return frame
        return despill_rgba(frame, self.strength)
