
from collections import OrderedDict


class FrameCache:
    """
    Cache frame berbasis waktu (detik)
    LRU + windowed
    """
    def __init__(self, max_frames=120):
        self.max_frames = max_frames
        self.cache = OrderedDict()

    def get(self, t):
        key = round(t, 3)
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, t, frame):
        key = round(t, 3)
        self.cache[key] = frame
        self.cache.move_to_end(key)

        if len(self.cache) > self.max_frames:
            self.cache.popitem(last=False)

    def clear(self):
        self.cache.clear()
