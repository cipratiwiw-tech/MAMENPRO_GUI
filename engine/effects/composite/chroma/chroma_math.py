import numpy as np
import cv2


def chroma_key_rgba(
    frame,
    key_color=(0, 255, 0),   # BGR
    threshold=40,
    softness=10
):
    """
    Apply chroma key and return BGRA frame.
    - frame: BGR or BGRA (uint8)
    - key_color: (B, G, R)
    """

    if frame.ndim != 3 or frame.shape[2] not in (3, 4):
        return frame

    # Convert to BGR
    if frame.shape[2] == 4:
        bgr = frame[:, :, :3].astype(np.float32)
    else:
        bgr = frame.astype(np.float32)

    key = np.array(key_color, dtype=np.float32)

    # Distance from key color
    diff = np.linalg.norm(bgr - key, axis=2)

    # Alpha mask
    alpha = np.clip(
        (diff - threshold) / max(softness, 1e-5),
        0.0,
        1.0
    )

    alpha = (alpha * 255).astype(np.uint8)

    # Build BGRA
    bgra = np.zeros((bgr.shape[0], bgr.shape[1], 4), dtype=np.uint8)
    bgra[:, :, :3] = np.clip(bgr, 0, 255).astype(np.uint8)
    bgra[:, :, 3] = alpha

    return bgra
