import numpy as np


def despill_rgba(bgra, strength=0.5):
    """
    Reduce green spill on BGRA frame.
    - bgra: BGRA uint8
    - strength: 0.0 – 1.0
    """

    if bgra.ndim != 3 or bgra.shape[2] != 4:
        return bgra

    strength = float(np.clip(strength, 0.0, 1.0))

    rgb = bgra[:, :, :3].astype(np.float32)
    alpha = bgra[:, :, 3:4]

    b = rgb[:, :, 0]
    g = rgb[:, :, 1]
    r = rgb[:, :, 2]

    avg_rb = (r + b) * 0.5
    g_new = g * (1.0 - strength) + avg_rb * strength

    rgb[:, :, 1] = g_new
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)

    return np.concatenate([rgb, alpha], axis=2)
