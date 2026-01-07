from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, QSpinBox, 
                             QPushButton, QSlider, QGridLayout, QScrollArea, QCheckBox, QHBoxLayout, QColorDialog)
from PySide6.QtCore import Qt, Signal

class MediaTab(QScrollArea):
    sig_media_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(15)
        
        self._init_video_attributes() 
        self._init_frame_attributes() 
        
        self.layout.addStretch()
        self.setWidget(container)
        self._connect_signals()

    def _init_video_attributes(self):
        self.group_video = QGroupBox("VIDEO ATTRIBUTES (CLIP ONLY)")
        self.group_video.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        
        vbox = QVBoxLayout(self.group_video)
        vbox.setSpacing(15)

        # 1. TRANSFORM (CLIP)
        lbl_trans = QLabel("--- TRANSFORM ---")
        lbl_trans.setAlignment(Qt.AlignCenter)
        lbl_trans.setStyleSheet("color: #aaa; font-size: 10px; font-weight: bold;")
        vbox.addWidget(lbl_trans)

        grid_trans = QGridLayout()
        self.spn_scale = self._create_spinbox(1, 1000, 100, "%")
        self.spn_rot = self._create_spinbox(-360, 360, 0, "°") 
        self.spn_opacity = self._create_spinbox(0, 100, 100, "%")
        
        grid_trans.addWidget(QLabel("Scale:"), 0, 0); grid_trans.addWidget(self.spn_scale, 0, 1)
        grid_trans.addWidget(QLabel("Rotate:"), 0, 2); grid_trans.addWidget(self.spn_rot, 0, 3)
        grid_trans.addWidget(QLabel("Opacity:"), 1, 0); grid_trans.addWidget(self.spn_opacity, 1, 1)
        
        # Smart Frame (Crop)
        self.spn_sf_l = self._create_spinbox(0, 500, 0, " px")
        self.spn_sf_r = self._create_spinbox(0, 500, 0, " px")
        grid_trans.addWidget(QLabel("Crop L:"), 2, 0); grid_trans.addWidget(self.spn_sf_l, 2, 1)
        grid_trans.addWidget(QLabel("Crop R:"), 2, 2); grid_trans.addWidget(self.spn_sf_r, 2, 3)
        vbox.addLayout(grid_trans)

        # 2. COLOR CORRECTION
        lbl_color = QLabel("--- COLOR CORRECTION ---")
        lbl_color.setAlignment(Qt.AlignCenter)
        lbl_color.setStyleSheet("color: #aaa; font-size: 10px; font-weight: bold;")
        vbox.addWidget(lbl_color)

        grid_color = QGridLayout()
        self.slider_bright = self._create_slider(-100, 100, 0)
        self.slider_contrast = self._create_slider(-100, 100, 0)
        self.slider_sat = self._create_slider(0, 200, 100)
        self.slider_hue = self._create_slider(-180, 180, 0)

        grid_color.addWidget(QLabel("Bright:"), 0, 0); grid_color.addWidget(self.slider_bright, 0, 1)
        grid_color.addWidget(QLabel("Contr:"), 1, 0); grid_color.addWidget(self.slider_contrast, 1, 1)
        grid_color.addWidget(QLabel("Sat:"), 2, 0); grid_color.addWidget(self.slider_sat, 2, 1)
        grid_color.addWidget(QLabel("Hue:"), 3, 0); grid_color.addWidget(self.slider_hue, 3, 1)
        vbox.addLayout(grid_color)

        # 3. CHROMA KEY
        lbl_chroma = QLabel("--- CHROMA KEY ---")
        lbl_chroma.setAlignment(Qt.AlignCenter)
        lbl_chroma.setStyleSheet("color: #aaa; font-size: 10px; font-weight: bold;")
        vbox.addWidget(lbl_chroma)
        
        grid_chroma = QGridLayout()
        self.btn_pick_color = QPushButton("Pick Color")
        self.btn_pick_color.setStyleSheet("background-color: #00ff00; color: black;")
        self.chroma_color_hex = "#00ff00"
        self.btn_pick_color.clicked.connect(self._pick_chroma_color)
        
        self.spn_sim = self._create_spinbox(1, 500, 100)
        self.spn_smooth = self._create_spinbox(0, 200, 10)
        self.spn_spill_r = self._create_spinbox(-100, 100, 0)
        self.spn_spill_g = self._create_spinbox(-100, 100, 0)
        self.spn_spill_b = self._create_spinbox(-100, 100, 0)
        
        grid_chroma.addWidget(self.btn_pick_color, 0, 0, 1, 2)
        grid_chroma.addWidget(QLabel("Sim:"), 1, 0); grid_chroma.addWidget(self.spn_sim, 1, 1)
        grid_chroma.addWidget(QLabel("Smooth:"), 1, 2); grid_chroma.addWidget(self.spn_smooth, 1, 3)
        grid_chroma.addWidget(QLabel("Spill R:"), 2, 0); grid_chroma.addWidget(self.spn_spill_r, 2, 1)
        grid_chroma.addWidget(QLabel("Spill G:"), 2, 2); grid_chroma.addWidget(self.spn_spill_g, 2, 3)
        grid_chroma.addWidget(QLabel("Spill B:"), 3, 0); grid_chroma.addWidget(self.spn_spill_b, 3, 1)
        vbox.addLayout(grid_chroma)
        
        self.layout.addWidget(self.group_video)

    def _init_frame_attributes(self):
        self.group_frame = QGroupBox("FRAME ATTRIBUTES (CONTAINER)")
        self.group_frame.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #0984e3; margin-top: 10px; } QGroupBox::title { color: #0984e3; }")
        
        grid = QGridLayout(self.group_frame)
        grid.setSpacing(10)
        
        self.spn_x = self._create_spinbox(-5000, 5000, 0, " px")
        self.spn_y = self._create_spinbox(-5000, 5000, 0, " px")
        grid.addWidget(QLabel("Pos X:"), 0, 0); grid.addWidget(self.spn_x, 0, 1)
        grid.addWidget(QLabel("Pos Y:"), 0, 2); grid.addWidget(self.spn_y, 0, 3)
        
        self.spn_frame_w = self._create_spinbox(10, 5000, 540, " px")
        self.spn_frame_h = self._create_spinbox(10, 5000, 960, " px")
        grid.addWidget(QLabel("Width:"), 1, 0); grid.addWidget(self.spn_frame_w, 1, 1)
        grid.addWidget(QLabel("Height:"), 1, 2); grid.addWidget(self.spn_frame_h, 1, 3)
        
        self.spn_frame_rot = self._create_spinbox(-360, 360, 0, "°")
        # [FIX] Rename ke chk_lock_frame agar SettingPanel lama tidak error
        self.chk_lock_frame = QCheckBox("Lock Frame") 
        
        grid.addWidget(QLabel("Rotation:"), 2, 0); grid.addWidget(self.spn_frame_rot, 2, 1)
        grid.addWidget(self.chk_lock_frame, 2, 2, 1, 2)
        
        self.layout.addWidget(self.group_frame)

    def _create_spinbox(self, min_v, max_v, val, suffix=""):
        sb = QSpinBox()
        sb.setRange(min_v, max_v); sb.setValue(val); sb.setSuffix(suffix)
        return sb
        
    def _create_slider(self, min_v, max_v, val):
        sl = QSlider(Qt.Horizontal); sl.setRange(min_v, max_v); sl.setValue(val)
        return sl

    def _pick_chroma_color(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.chroma_color_hex = c.name()
            self.btn_pick_color.setStyleSheet(f"background-color: {self.chroma_color_hex}; color: black;")
            self._emit_change()

    def _connect_signals(self):
        # Frame
        self.spn_x.valueChanged.connect(self._emit_change)
        self.spn_y.valueChanged.connect(self._emit_change)
        self.spn_frame_w.valueChanged.connect(self._emit_change)
        self.spn_frame_h.valueChanged.connect(self._emit_change)
        self.spn_frame_rot.valueChanged.connect(self._emit_change)
        self.chk_lock_frame.toggled.connect(self._emit_change) # Update connect
    #     self.chk_lock_frame.toggled.connect(self._handle_lock_ui)

    # # Tambahkan method baru ini di dalam class MediaTab
    # def _handle_lock_ui(self, is_locked):
    #     enabled = not is_locked
    #     self.spn_x.setEnabled(enabled)
    #     self.spn_y.setEnabled(enabled)
    #     self.spn_frame_w.setEnabled(enabled)
    #     self.spn_frame_h.setEnabled(enabled)
    #     self.spn_frame_rot.setEnabled(enabled)
        
    #     # Transform
    #     self.spn_scale.valueChanged.connect(self._emit_change)
    #     self.spn_rot.valueChanged.connect(self._emit_change)
    #     self.spn_opacity.valueChanged.connect(self._emit_change)
    #     self.spn_sf_l.valueChanged.connect(self._emit_change)
    #     self.spn_sf_r.valueChanged.connect(self._emit_change)
        
    #     # Color & Chroma
    #     self.slider_bright.valueChanged.connect(self._emit_change)
    #     self.slider_contrast.valueChanged.connect(self._emit_change)
    #     self.slider_sat.valueChanged.connect(self._emit_change)
    #     self.slider_hue.valueChanged.connect(self._emit_change)
    #     self.spn_sim.valueChanged.connect(self._emit_change)
    #     self.spn_smooth.valueChanged.connect(self._emit_change)
    #     self.spn_spill_r.valueChanged.connect(self._emit_change)
    #     self.spn_spill_g.valueChanged.connect(self._emit_change)
    #     self.spn_spill_b.valueChanged.connect(self._emit_change)

    def _emit_change(self):
        data = {
            "x": self.spn_x.value(), "y": self.spn_y.value(),
            "frame_w": self.spn_frame_w.value(), "frame_h": self.spn_frame_h.value(),
            "frame_rot": self.spn_frame_rot.value(), "lock": self.chk_lock_frame.isChecked(),
            "scale": self.spn_scale.value(), "rot": self.spn_rot.value(), "opacity": self.spn_opacity.value(),
            "sf_l": self.spn_sf_l.value(), "sf_r": self.spn_sf_r.value(),
            "bright": self.slider_bright.value(), "contrast": self.slider_contrast.value(),
            "sat": self.slider_sat.value(), "hue": self.slider_hue.value(),
            "chroma_key": self.chroma_color_hex, "similarity": self.spn_sim.value(),
            "smoothness": self.spn_smooth.value(),
            "spill_r": self.spn_spill_r.value(), "spill_g": self.spn_spill_g.value(), "spill_b": self.spn_spill_b.value()
        }
        self.sig_media_changed.emit(data)

    def set_values(self, data):
        self.blockSignals(True)
        is_bg = data.get("is_bg", False)
        self.group_video.setEnabled(not is_bg)
        self.group_video.setTitle("VIDEO ATTRIBUTES (DISABLED FOR BG)" if is_bg else "VIDEO ATTRIBUTES (CLIP ONLY)")
        
        if "x" in data: self.spn_x.setValue(data["x"])
        if "y" in data: self.spn_y.setValue(data["y"])
        if "frame_w" in data: self.spn_frame_w.setValue(data["frame_w"])
        if "frame_h" in data: self.spn_frame_h.setValue(data["frame_h"])
        if "frame_rot" in data: self.spn_frame_rot.setValue(data["frame_rot"])
        if "lock" in data: self.chk_lock_frame.setChecked(data["lock"])

        if "scale" in data: self.spn_scale.setValue(data["scale"])
        if "rot" in data: self.spn_rot.setValue(data["rot"])
        if "opacity" in data: self.spn_opacity.setValue(data["opacity"])
        if "sf_l" in data: self.spn_sf_l.setValue(data["sf_l"])
        if "sf_r" in data: self.spn_sf_r.setValue(data["sf_r"])
        
        if "bright" in data: self.slider_bright.setValue(data["bright"])
        if "contrast" in data: self.slider_contrast.setValue(data["contrast"])
        if "sat" in data: self.slider_sat.setValue(data["sat"])
        if "hue" in data: self.slider_hue.setValue(data["hue"])
        
        if "chroma_key" in data:
            self.chroma_color_hex = data["chroma_key"]
            self.btn_pick_color.setStyleSheet(f"background-color: {self.chroma_color_hex}; color: black;")
        if "similarity" in data: self.spn_sim.setValue(data["similarity"])
        if "smoothness" in data: self.spn_smooth.setValue(data["smoothness"])
        
        self.blockSignals(False)