from collections import OrderedDict

class FrameCache:
    """
    Cache frame.
    [MODIFIED] Sekarang menerima key apa saja (str/float), 
    tidak lagi memaksakan round(t) di dalam method get/put.
    """
    def __init__(self, max_frames=120):
        self.max_frames = max_frames
        self.cache = OrderedDict()

    def get(self, key):
        # HAPUS: key = round(t, 3) 
        # GANTI JADI:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key, frame):
        # HAPUS: key = round(t, 3)
        # GANTI JADI:
        self.cache[key] = frame
        self.cache.move_to_end(key)

        if len(self.cache) > self.max_frames:
            self.cache.popitem(last=False)

    def clear(self):
        self.cache.clear()