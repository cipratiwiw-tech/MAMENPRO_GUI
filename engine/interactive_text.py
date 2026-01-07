from engine.interaction.interactive import InteractiveLayerMixin
from effects.text.text_advanced import TextAdvancedEffect

class InteractiveTextLayer(InteractiveLayerMixin, TextAdvancedEffect):
    """
    Wrapper GUI untuk TextAdvancedEffect
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
