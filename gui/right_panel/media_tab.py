from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                             QLabel, QSpinBox, QPushButton, QSlider, QScrollArea, QCheckBox)
from PySide6.QtCore import Qt

class MediaTab(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        container = QWidget()
        self.layout = QVBoxLayout(container)
        
        self._init_transform()
        self._init_visual()
        self._init_chroma()
        self._init_frame_setting() # <-- Grup baru ditambahkan di sini
        
        self.layout.addStretch()
        self.setWidget(container)

    def _init_transform(self):
        group = QGroupBox("TRANSFORM & POSISI")
        grid = QGridLayout(group)
        
        self.spn_x = QSpinBox(); self.spn_x.setRange(-5000, 5000); self.spn_x.setPrefix("X: ")
        self.spn_y = QSpinBox(); self.spn_y.setRange(-5000, 5000); self.spn_y.setPrefix("Y: ")
        self.spn_scale = QSpinBox(); self.spn_scale.setRange(1, 1000); self.spn_scale.setValue(100); self.spn_scale.setSuffix("%")
        self.spn_rot = QSpinBox(); self.spn_rot.setRange(-360, 360); self.spn_rot.setSuffix("°")
        self.spn_opacity = QSpinBox(); self.spn_opacity.setRange(0, 100); self.spn_opacity.setValue(100); self.spn_opacity.setSuffix("%")

        # --- Tambahan Input SF-L & SF-R ---
        self.spn_sf_l = QSpinBox(); self.spn_sf_l.setRange(-1000, 1000); self.spn_sf_l.setPrefix("SF-L: ")
        self.spn_sf_r = QSpinBox(); self.spn_sf_r.setRange(-1000, 1000); self.spn_sf_r.setPrefix("SF-R: ")

        grid.addWidget(self.spn_x, 0, 0); grid.addWidget(self.spn_y, 0, 1)
        grid.addWidget(self.spn_scale, 1, 0); grid.addWidget(self.spn_rot, 1, 1)
        grid.addWidget(QLabel("Opacity:"), 2, 0); grid.addWidget(self.spn_opacity, 2, 1)
        
        # Menambahkan SF di baris ke-3
        grid.addWidget(self.spn_sf_l, 3, 0)
        grid.addWidget(self.spn_sf_r, 3, 1)
        
        self.layout.addWidget(group)

    def _init_visual(self):
        group = QGroupBox("COLOR CORRECTION")
        grid = QGridLayout(group)
        
        self.spn_bright = QSpinBox(); self.spn_bright.setRange(-100, 100)
        self.spn_contrast = QSpinBox(); self.spn_contrast.setRange(-100, 100)
        self.spn_sat = QSpinBox(); self.spn_sat.setRange(-100, 100)
        self.spn_hue = QSpinBox(); self.spn_hue.setRange(-180, 180)
        
        grid.addWidget(QLabel("Brightness"), 0, 0); grid.addWidget(self.spn_bright, 0, 1)
        grid.addWidget(QLabel("Contrast"), 1, 0); grid.addWidget(self.spn_contrast, 1, 1)
        grid.addWidget(QLabel("Saturation"), 2, 0); grid.addWidget(self.spn_sat, 2, 1)
        grid.addWidget(QLabel("Hue"), 3, 0); grid.addWidget(self.spn_hue, 3, 1)
        
        self.layout.addWidget(group)

    def _init_chroma(self):
        group = QGroupBox("CHROMA KEY (GREEN SCREEN)")
        grid = QGridLayout(group)
        
        # Komponen lama
        self.btn_pick = QPushButton("Pick Color")
        self.spn_sim = QSpinBox(); self.spn_sim.setPrefix("Sim: ")
        self.spn_smooth = QSpinBox(); self.spn_smooth.setPrefix("Smooth: ")
        
        # Tambahan Slider RGB
        self.lbl_r = QLabel("R")
        self.slider_r = QSlider(Qt.Horizontal); self.slider_r.setRange(0, 255)
        self.spn_r = QSpinBox(); self.spn_r.setRange(0, 255)
        
        self.lbl_g = QLabel("G")
        self.slider_g = QSlider(Qt.Horizontal); self.slider_g.setRange(0, 255)
        self.spn_g = QSpinBox(); self.spn_g.setRange(0, 255)

        self.lbl_b = QLabel("B")
        self.slider_b = QSlider(Qt.Horizontal); self.slider_b.setRange(0, 255)
        self.spn_b = QSpinBox(); self.spn_b.setRange(0, 255)

        # Menyusun Layout (Grid 3 kolom)
        grid.addWidget(self.btn_pick, 0, 0, 1, 3)
        grid.addWidget(self.spn_sim, 1, 0, 1, 2)
        grid.addWidget(self.spn_smooth, 1, 2)
        
        grid.addWidget(self.lbl_r, 2, 0); grid.addWidget(self.slider_r, 2, 1); grid.addWidget(self.spn_r, 2, 2)
        grid.addWidget(self.lbl_g, 3, 0); grid.addWidget(self.slider_g, 3, 1); grid.addWidget(self.spn_g, 3, 2)
        grid.addWidget(self.lbl_b, 4, 0); grid.addWidget(self.slider_b, 4, 1); grid.addWidget(self.spn_b, 4, 2)
        
        self.layout.addWidget(group)

        # Connect Slider <-> SpinBox
        self.slider_r.valueChanged.connect(self.spn_r.setValue)
        self.spn_r.valueChanged.connect(self.slider_r.setValue)
        self.slider_g.valueChanged.connect(self.spn_g.setValue)
        self.spn_g.valueChanged.connect(self.slider_g.setValue)
        self.slider_b.valueChanged.connect(self.spn_b.setValue)
        self.spn_b.valueChanged.connect(self.slider_b.setValue)

    def _init_frame_setting(self):
        """Grup baru untuk setting Frame Size, Rotation dan Lock"""
        group = QGroupBox("FRAME SETTING")
        grid = QGridLayout(group)
        
        # Size (Width & Height)
        self.spn_frame_w = QSpinBox(); self.spn_frame_w.setRange(1, 10000); self.spn_frame_w.setPrefix("W: ")
        self.spn_frame_h = QSpinBox(); self.spn_frame_h.setRange(1, 10000); self.spn_frame_h.setPrefix("H: ")
        
        # Rotation
        self.spn_frame_rot = QSpinBox(); self.spn_frame_rot.setRange(-360, 360); self.spn_frame_rot.setPrefix("Rot: "); self.spn_frame_rot.setSuffix("°")
        
        # Toggle Lock Frame
        self.chk_lock_frame = QCheckBox("Lock Frame")
        
        # Layouting
        grid.addWidget(self.spn_frame_w, 0, 0)
        grid.addWidget(self.spn_frame_h, 0, 1)
        grid.addWidget(self.spn_frame_rot, 1, 0)
        grid.addWidget(self.chk_lock_frame, 1, 1)
        
        self.layout.addWidget(group)
        
# ... (kode class PreviewPanel di atas) ...

# TAMBAHAN DI BAWAH FILE:
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    # Bungkus panel kamu dalam window dummy
    window = QWidget() # Atau QMainWindow
    layout = QVBoxLayout(window)
    
    # PANGGIL PANEL YANG LAGI DIEDIT
    panel = MediaTab() 
    layout.addWidget(panel)
    
    window.resize(800, 600) # Ukuran sementara
    window.show()
    
    # Bisa tambahkan data palsu (mock data) buat ngetes
    # panel.set_status("Mode Testing...") 
    
    sys.exit(app.exec())