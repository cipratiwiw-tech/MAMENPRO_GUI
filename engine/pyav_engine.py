
import av
from engine.frame_cache import FrameCache


class PyAVClip:
    def __init__(self, path, fps=30):
        self.container = av.open(path)
        
        if len(self.container.streams.video) == 0:
            raise ValueError(f"File tidak memiliki stream video: {path}")
        
        self.stream = self.container.streams.video[0]
        self.stream.thread_type = "AUTO"
        self.time_base = float(self.stream.time_base)

        # --- TAMBAHKAN LOGIKA DURASI DI SINI ---
        # Container.duration biasanya dalam mikrosekon (1/1.000.000)
        if self.container.duration:
            self.duration = float(self.container.duration / av.time_base)
        elif self.stream.duration:
            self.duration = float(self.stream.duration * self.time_base)
        else:
            self.duration = 0.0
        # ---------------------------------------

        self.fps = fps
        self.cache = FrameCache(max_frames=180)

    def _decode_frame(self, t):
        pts = int(t / self.time_base)
        self.container.seek(
            pts,
            stream=self.stream,
            any_frame=False,
            backward=True
        )

        for frame in self.container.decode(self.stream):
            ft = frame.pts * self.time_base
            if ft >= t:
                return frame.to_ndarray(format="rgb24")
        return None

    def get_frame_at(self, t):
        cached = self.cache.get(t)
        if cached is not None:
            return cached

        frame = self._decode_frame(t)
        if frame is not None:
            self.cache.put(t, frame)

        return frame

    def prefetch(self, start_t, duration=1.0):
        """
        Prefetch frame ke depan (1 detik default)
        """
        step = 1.0 / self.fps
        t = start_t

        for _ in range(int(duration * self.fps)):
            if self.cache.get(t) is None:
                frame = self._decode_frame(t)
                if frame is not None:
                    self.cache.put(t, frame)
            t += step
