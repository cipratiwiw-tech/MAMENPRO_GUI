# engine/dummy_engine.py
import numpy as np

class DummyEngine:
    """
    Mesin palsu untuk pengembangan UI.
    Tidak memproses video, hanya mencetak log ke terminal.
    """
    def __init__(self):
        print("[ENGINE] Dummy Engine Started (UI Mode)")
        self.clips = []

    def sync_clips(self, clips):
        self.clips = clips
        print(f"[ENGINE] Syncing {len(clips)} clips from GUI...")
        for i, clip in enumerate(clips):
            print(f"  > Clip {i}: {clip.name} (File: {clip.file_path})")

    def get_frame_at(self, t):
        # Kembalikan frame hitam kosong (1920x1080) agar PreviewPanel tidak error
        # Format: (Height, Width, Channel)
        return np.zeros((1080, 1920, 3), dtype=np.uint8)