# engine/preview_engine.py
from PySide6.QtCore import QObject, QTimer, Signal

class PreviewEngine(QObject):
    """
    PlaybackEngine / Master Clock.
    Tugas: Mengelola waktu (play, pause, seek, tick).
    Haram: Tahu soal Layer, Rendering, atau Audio Processing (untuk saat ini).
    """
    
    # Mengirim waktu saat ini (detik) setiap frame
    sig_tick = Signal(float)
    
    # Mengirim status playback (True=Playing, False=Paused)
    sig_playback_state = Signal(bool)

    def __init__(self, fps=30):
        super().__init__()
        self._fps = fps
        self._interval = int(1000 / fps)  # ms per frame
        
        self._current_time = 0.0
        self._duration = 10.0  # Default duration limit
        
        # Timer Murni: Hanya untuk detak jantung waktu
        self._timer = QTimer()
        self._timer.setTimerType(Qt.PreciseTimer) if 'Qt' in globals() else None
        self._timer.timeout.connect(self._on_tick)
        self._timer.setInterval(self._interval)

    @property
    def current_time(self) -> float:
        return self._current_time

    @property
    def is_playing(self) -> bool:
        return self._timer.isActive()

    def set_duration(self, duration: float):
        """Menentukan batas akhir timeline agar player tahu kapan harus stop/loop."""
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
        """Memindahkan 'jarum' waktu secara manual (Scrubbing)."""
        # Clamp waktu agar tidak keluar batas durasi
        safe_t = max(0.0, min(t, self._duration))
        self._current_time = safe_t
        
        # Paksa emit signal agar UI/Render update ke posisi baru
        self.sig_tick.emit(self._current_time)

    def _on_tick(self):
        """
        Detak jantung internal.
        Dipanggil oleh QTimer setiap X milidetik.
        """
        step = 1.0 / self._fps
        next_time = self._current_time + step

        # Logic Loop Sederhana
        if next_time >= self._duration:
            self._current_time = 0.0
            # Opsional: self.pause() jika tidak ingin looping
        else:
            self._current_time = next_time

        # TERIAK WAKTU KE LUAR (Controller yang dengar)
        self.sig_tick.emit(self._current_time)