# engine/preview_engine.py
from PySide6.QtCore import QObject, QTimer, Signal, Qt # <--- Import Qt eksplisit

class PreviewEngine(QObject):
    sig_tick = Signal(float)
    sig_playback_state = Signal(bool)

    def __init__(self, fps=30):
        super().__init__()
        self._fps = fps
        self._interval = int(1000 / fps)
        
        self._current_time = 0.0
        self._duration = 10.0
        
        self._timer = QTimer()
        self._timer.setTimerType(Qt.PreciseTimer) # <--- API Bersih
        self._timer.timeout.connect(self._on_tick)
        self._timer.setInterval(self._interval)

    @property
    def current_time(self) -> float:
        return self._current_time

    @property
    def is_playing(self) -> bool:
        return self._timer.isActive()

    def set_duration(self, duration: float):
        self._duration = max(0.1, duration)

    def play(self):
        if not self.is_playing:
            self._timer.start()
            self.sig_playback_state.emit(True)

    def pause(self):
        if self.is_playing:
            self._timer.stop()
            self.sig_playback_state.emit(False)

    def toggle_play(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def seek(self, t: float):
        safe_t = max(0.0, min(t, self._duration))
        self._current_time = safe_t
        self.sig_tick.emit(self._current_time)

    def _on_tick(self):
        step = 1.0 / self._fps
        next_time = self._current_time + step

        if next_time >= self._duration:
            self._current_time = 0.0
            # self.pause() # Uncomment jika ingin stop di akhir
        else:
            self._current_time = next_time

        self.sig_tick.emit(self._current_time)