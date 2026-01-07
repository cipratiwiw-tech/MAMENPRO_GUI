# engine/preview/preview_engine.py
from PySide6.QtCore import QObject, QTimer, Signal
from engine.background_layer_pyav import BackgroundLayer



class PreviewEngine(QObject):
    sig_time_changed = Signal(float)  # Mengirimkan waktu dalam detik (float)
    sig_state_changed = Signal(bool) # True = Playing, False = Paused

    def __init__(self, fps=30):
        super().__init__()
        self.fps = fps
        self.current_time = 0.0
        self.duration = 0.0
        
        self.bg_layer = BackgroundLayer()
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_tick)
        self.timer.setInterval(1000 / self.fps) # Misal 33ms untuk 30fps
        


    def _on_tick(self):
        self.current_time += 1.0 / self.fps
        if self.current_time >= self.duration:
            self.current_time = 0.0 # Loop atau stop
            
        self.sig_time_changed.emit(self.current_time)

    def set_time(self, seconds):
        """Update waktu secara manual (saat scrubbing slider)"""
        self.current_time = max(0.0, min(seconds, self.duration))
        self.sig_time_changed.emit(self.current_time)

    def toggle_play(self):
        if self.timer.isActive():
            self.timer.stop()
            self.sig_state_changed.emit(False)
        else:
            if self.duration > 0:
                self.timer.start()
                self.sig_state_changed.emit(True)

    def set_duration(self, seconds):
        self.duration = seconds