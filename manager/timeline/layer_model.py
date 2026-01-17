from dataclasses import dataclass, field
from typing import Dict, Any
from .time_range import TimeRange

@dataclass
class LayerModel:
    """
    Model data layer yang ringan untuk kalkulasi timeline.
    Tidak mengandung referensi ke Widget UI atau Image Buffer.
    """
    id: str
    type: str          # 'video', 'audio', 'text', dll
    time: TimeRange    # Rentang waktu aktif
    z_index: int = 0   # Urutan tumpukan (opsional tapi penting buat sorting nanti)
    
    # Payload bisa berisi path file, teks konten, dll.
    # Engine timeline tidak perlu tahu isinya, cuma perlu menyimpannya.
    payload: Dict[str, Any] = field(default_factory=dict)