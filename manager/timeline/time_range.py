from dataclasses import dataclass

@dataclass(frozen=True)
class TimeRange:
    """
    Value Object yang merepresentasikan rentang waktu.
    Immutable (frozen=True) agar aman dan tidak berubah tak sengaja.
    """
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start

    def contains(self, t: float) -> bool:
        """Mengecek apakah waktu t berada dalam rentang [start, end)."""
        return self.start <= t < self.end