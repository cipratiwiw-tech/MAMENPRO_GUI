from engine.core.layer_base import Layer
from effects.composite.chroma.chroma_math import chroma_key_rgba


class ChromaKeyEffect(Layer):
    def __init__(self, key_color=(0,255,0), threshold=40, softness=10, z_index=0, enabled=True):
        super().__init__(z_index=z_index, enabled=enabled, name="ChromaKey")
        self.key_color = key_color
        self.threshold = threshold
        self.softness = softness


    def apply(self, frame, frame_index, fps, context):
        out = chroma_key_rgba(
            frame,
            self.key_color,
            self.threshold,
            self.softness
        )
        context["force_bgra"] = True
        return out
