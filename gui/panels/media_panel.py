from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, QSpinBox, 
                             QPushButton, QSlider, QGridLayout, QScrollArea, QCheckBox, QHBoxLayout, QColorDialog, QDoubleSpinBox, QAbstractSpinBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics, QCursor

class MediaTab(QScrollArea):
    sig_media_changed = Signal(dict)
    sig_pipette_toggled = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        container = QWidget()
        container.setStyleSheet("background-color: #23272e;") 
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(8, 8, 8, 8) 
        
        # [STYLE] Compact Input
        self.spinbox_style = """
            QSpinBox, QDoubleSpinBox {
                background-color: #2b2b2b;
                color: #dcdcdc;
                border: 1px solid #3e4451;
                border-radius: 2px;
                padding-left: 0px;  
                padding-right: 4px; 
                margin: 0px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #56b6c2;
                background-color: #1e1e1e;
            }
        """

        self._init_time_attributes()
        self._init_video_attributes() 
        self._init_frame_attributes() 
        
        self.layout.addStretch()
        self.setWidget(container)
        self._connect_signals()
    
    def _create_label(self, text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet("color: #abb2bf; font-size: 11px; margin-right: 4px;") 
        return lbl

    def _optimize_width(self, sb, min_val, max_val, suffix):
        if isinstance(sb, QDoubleSpinBox):
            prec = sb.decimals()
            s_min = f"{min_val:.{prec}f}{suffix}"
            s_max = f"{max_val:.{prec}f}{suffix}"
        else:
            s_min = f"{min_val}{suffix}"
            s_max = f"{max_val}{suffix}"
            
        longest_text = s_max if len(s_max) > len(s_min) else s_min
        fm = sb.fontMetrics()
        text_width = fm.horizontalAdvance(longest_text)
        
        final_width = max(45, text_width + 24)
        sb.setFixedWidth(final_width)

    def _style_spinbox(self, sb, min_v, max_v, suffix):
        sb.setButtonSymbols(QAbstractSpinBox.NoButtons) 
        sb.setAlignment(Qt.AlignRight) 
        sb.setStyleSheet(self.spinbox_style)
        self._optimize_width(sb, min_v, max_v, suffix)

    def _init_time_attributes(self):
        self.group_time = QGroupBox("TIMING")
        self.group_time.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #e5c07b; margin-top: 6px; color: #e5c07b; }")
        
        grid = QGridLayout(self.group_time)
        grid.setSpacing(8)
        grid.setContentsMargins(5, 10, 5, 5)
        
        self.spn_start = QDoubleSpinBox()
        self.spn_start.setRange(0.0, 36000.0)
        self.spn_start.setSingleStep(0.1)
        self.spn_start.setSuffix("s") 
        self._style_spinbox(self.spn_start, 0.0, 36000.0, "s")
        
        self.spn_end = QDoubleSpinBox()
        self.spn_end.setRange(0.0, 36000.0)
        self.spn_end.setSingleStep(0.1)
        self.spn_end.setSuffix("s")
        self.spn_end.setValue(5.0)
        self._style_spinbox(self.spn_end, 0.0, 36000.0, "s")
        
        grid.addWidget(self._create_label("Start:"), 0, 0)
        grid.addWidget(self.spn_start, 0, 1)
        grid.addWidget(self._create_label("End:"), 0, 2)
        grid.addWidget(self.spn_end, 0, 3)
        
        grid.setColumnStretch(4, 1) 
        self.layout.addWidget(self.group_time)
        
    def _init_video_attributes(self):
        self.group_video = QGroupBox("CLIP ATTRIBUTES")
        self.group_video.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #56b6c2; margin-top: 6px; color: #56b6c2; }")
        
        vbox = QVBoxLayout(self.group_video)
        vbox.setSpacing(12)
        vbox.setContentsMargins(5, 10, 5, 5)

        # 1. TRANSFORM
        lbl_trans = QLabel("TRANSFORM")
        lbl_trans.setAlignment(Qt.AlignCenter)
        lbl_trans.setStyleSheet("color: #5c6370; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        vbox.addWidget(lbl_trans)

        grid_trans = QGridLayout()
        grid_trans.setVerticalSpacing(8)
        grid_trans.setHorizontalSpacing(10)
        
        self.spn_scale = self._create_spinbox(1, 1000, 100, "%")
        self.spn_rot = self._create_spinbox(-360, 360, 0, "°") 
        self.spn_opacity = self._create_spinbox(0, 100, 100, "%")
        
        # Row 0
        grid_trans.addWidget(self._create_label("Scale:"), 0, 0)
        grid_trans.addWidget(self.spn_scale, 0, 1)
        grid_trans.addWidget(self._create_label("Rotate:"), 0, 2)
        grid_trans.addWidget(self.spn_rot, 0, 3)
        
        # Row 1
        grid_trans.addWidget(self._create_label("Opacity:"), 1, 0)
        grid_trans.addWidget(self.spn_opacity, 1, 1)
        
        # Row 2: SF-L & SF-R (CROP)
        self.spn_sf_l = self._create_spinbox(0, 500, 0, "px")
        self.spn_sf_r = self._create_spinbox(0, 500, 0, "px")
        
        grid_trans.addWidget(self._create_label("Crop L:"), 2, 0)
        grid_trans.addWidget(self.spn_sf_l, 2, 1)
        grid_trans.addWidget(self._create_label("Crop R:"), 2, 2)
        grid_trans.addWidget(self.spn_sf_r, 2, 3)

        # [MODIFIKASI] Row 3: Feather L, R, T, B
        # Agar rapi, kita buat Grid khusus atau masukkan ke grid utama
        # Kita gunakan baris 3 dan 4 untuk Feather agar jelas
        
        self.spn_f_l = self._create_spinbox(0, 200, 0, "px")
        self.spn_f_r = self._create_spinbox(0, 200, 0, "px")
        self.spn_f_t = self._create_spinbox(0, 200, 0, "px")
        self.spn_f_b = self._create_spinbox(0, 200, 0, "px")

        # Label Sub-Header Feather
        lbl_feather = QLabel("- FEATHER EDGE -")
        lbl_feather.setAlignment(Qt.AlignCenter)
        lbl_feather.setStyleSheet("color: #5c6370; font-size: 9px; font-weight: bold; margin-top:5px;")
        grid_trans.addWidget(lbl_feather, 3, 0, 1, 4)

        # Feather Inputs
        grid_trans.addWidget(self._create_label("Feath L:"), 4, 0)
        grid_trans.addWidget(self.spn_f_l, 4, 1)
        grid_trans.addWidget(self._create_label("Feath R:"), 4, 2)
        grid_trans.addWidget(self.spn_f_r, 4, 3)
        
        grid_trans.addWidget(self._create_label("Feath T:"), 5, 0)
        grid_trans.addWidget(self.spn_f_t, 5, 1)
        grid_trans.addWidget(self._create_label("Feath B:"), 5, 2)
        grid_trans.addWidget(self.spn_f_b, 5, 3)
        
        grid_trans.setColumnStretch(1, 0) 
        grid_trans.setColumnStretch(3, 0)
        grid_trans.setColumnStretch(4, 1) 

        vbox.addLayout(grid_trans)

        # 2. COLOR CORRECTION
        lbl_color = QLabel("COLOR CORRECTION")
        lbl_color.setAlignment(Qt.AlignCenter)
        lbl_color.setStyleSheet("color: #5c6370; font-size: 10px; font-weight: bold; letter-spacing: 1px; margin-top: 5px;")
        vbox.addWidget(lbl_color)

        grid_color = QGridLayout()
        grid_color.setSpacing(8)
        
        self.slider_bright = self._create_slider(-100, 100, 0)
        self.slider_contrast = self._create_slider(-100, 100, 0)
        self.slider_sat = self._create_slider(0, 200, 100)
        self.slider_hue = self._create_slider(-180, 180, 0)

        grid_color.addWidget(self._create_label("Bright:"), 0, 0)
        grid_color.addWidget(self.slider_bright, 0, 1)
        grid_color.addWidget(self._create_label("Contr:"), 1, 0)
        grid_color.addWidget(self.slider_contrast, 1, 1)
        grid_color.addWidget(self._create_label("Sat:"), 2, 0)
        grid_color.addWidget(self.slider_sat, 2, 1)
        grid_color.addWidget(self._create_label("Hue:"), 3, 0)
        grid_color.addWidget(self.slider_hue, 3, 1)
        
        vbox.addLayout(grid_color)

        # 3. CHROMA KEY
        lbl_chroma = QLabel("CHROMA KEY")
        lbl_chroma.setAlignment(Qt.AlignCenter)
        lbl_chroma.setStyleSheet("color: #5c6370; font-size: 10px; font-weight: bold; letter-spacing: 1px; margin-top: 5px;")
        vbox.addWidget(lbl_chroma)
        
        hbox_btns = QHBoxLayout()
        hbox_btns.setSpacing(5)
        
        self.btn_pick_color = QPushButton("Pick Screen Color")
        self.btn_pick_color.setStyleSheet("""
            QPushButton { background-color: #98c379; color: #282c34; font-weight: bold; border-radius: 3px; padding: 4px; }
            QPushButton:hover { background-color: #b5e890; }
        """)
        self.chroma_color_hex = "#00ff00"
        self.btn_pick_color.clicked.connect(self._pick_chroma_color)
        
        self.btn_pipette = QPushButton("🖊️") 
        self.btn_pipette.setFixedWidth(40)
        self.btn_pipette.setCheckable(True)
        self.btn_pipette.setToolTip("Pick Screen Color (Pipette)")
        self.btn_pipette.setStyleSheet("""
            QPushButton { background-color: #3e4451; color: #dcdcdc; border-radius: 3px; font-size: 14px; }
            QPushButton:checked { background-color: #56b6c2; color: #282c34; border: 1px solid #56b6c2; }
            QPushButton:hover { background-color: #4b5263; }
        """)
        self.btn_pipette.toggled.connect(self._on_pipette_toggled)
        
        hbox_btns.addWidget(self.btn_pick_color, 1)
        hbox_btns.addWidget(self.btn_pipette, 0)
        
        vbox.addLayout(hbox_btns)

        grid_chroma_params = QGridLayout()
        grid_chroma_params.setSpacing(10)
        
        self.spn_sim = self._create_spinbox(1, 500, 100)
        self.spn_smooth = self._create_spinbox(0, 200, 10)
        
        grid_chroma_params.addWidget(self._create_label("Sim:"), 0, 0)
        grid_chroma_params.addWidget(self.spn_sim, 0, 1)
        grid_chroma_params.addWidget(self._create_label("Smooth:"), 0, 2)
        grid_chroma_params.addWidget(self.spn_smooth, 0, 3)
        grid_chroma_params.setColumnStretch(4, 1) 

        vbox.addLayout(grid_chroma_params)

        grid_chroma_sliders = QGridLayout()
        grid_chroma_sliders.setSpacing(8) 
        
        self.slider_spill_r = self._create_slider(-100, 100, 0)
        self.slider_spill_g = self._create_slider(-100, 100, 0)
        self.slider_spill_b = self._create_slider(-100, 100, 0)
        
        grid_chroma_sliders.addWidget(self._create_label("Spill R:"), 0, 0)
        grid_chroma_sliders.addWidget(self.slider_spill_r, 0, 1)
        
        grid_chroma_sliders.addWidget(self._create_label("Spill G:"), 1, 0)
        grid_chroma_sliders.addWidget(self.slider_spill_g, 1, 1)
        
        grid_chroma_sliders.addWidget(self._create_label("Spill B:"), 2, 0)
        grid_chroma_sliders.addWidget(self.slider_spill_b, 2, 1)
        
        vbox.addLayout(grid_chroma_sliders)

        self.layout.addWidget(self.group_video)

    def _init_frame_attributes(self):
        self.group_frame = QGroupBox("FRAME / CONTAINER")
        self.group_frame.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #61afef; margin-top: 6px; color: #61afef; }")
        
        grid = QGridLayout(self.group_frame)
        grid.setSpacing(10)
        grid.setContentsMargins(5, 10, 5, 5)
        
        self.spn_x = self._create_spinbox(-5000, 5000, 0, "px")
        self.spn_y = self._create_spinbox(-5000, 5000, 0, "px")
        
        grid.addWidget(self._create_label("X:"), 0, 0)
        grid.addWidget(self.spn_x, 0, 1)
        grid.addWidget(self._create_label("Y:"), 0, 2)
        grid.addWidget(self.spn_y, 0, 3)
        
        self.spn_frame_w = self._create_spinbox(10, 5000, 540, "px")
        self.spn_frame_h = self._create_spinbox(10, 5000, 960, "px")
        
        grid.addWidget(self._create_label("W:"), 1, 0)
        grid.addWidget(self.spn_frame_w, 1, 1)
        grid.addWidget(self._create_label("H:"), 1, 2)
        grid.addWidget(self.spn_frame_h, 1, 3)
        
        self.spn_frame_rot = self._create_spinbox(-360, 360, 0, "°")
        self.chk_lock_frame = QCheckBox("Lock") 
        self.chk_lock_frame.setStyleSheet("color: #abb2bf; font-size: 11px;")
        
        grid.addWidget(self._create_label("Rot:"), 2, 0)
        grid.addWidget(self.spn_frame_rot, 2, 1)
        grid.addWidget(self.chk_lock_frame, 2, 3)
        
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(3, 0)
        grid.setColumnStretch(4, 1)
        
        self.layout.addWidget(self.group_frame)

    def _create_spinbox(self, min_v, max_v, val, suffix=""):
        sb = QSpinBox()
        sb.setRange(min_v, max_v); sb.setValue(val); sb.setSuffix(suffix)
        self._style_spinbox(sb, min_v, max_v, suffix)
        return sb
        
    def _create_slider(self, min_v, max_v, val):
        sl = QSlider(Qt.Horizontal); sl.setRange(min_v, max_v); sl.setValue(val)
        sl.setStyleSheet("""
            QSlider::groove:horizontal { border: 1px solid #3e4451; height: 4px; background: #2c313a; border-radius: 2px; }
            QSlider::handle:horizontal { background: #56b6c2; border: 1px solid #56b6c2; width: 12px; height: 12px; margin: -5px 0; border-radius: 6px; }
        """)
        return sl

    def _pick_chroma_color(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.chroma_color_hex = c.name()
            self.btn_pick_color.setStyleSheet(f"background-color: {self.chroma_color_hex}; color: black; font-weight: bold; border-radius: 3px; padding: 4px;")
            self._emit_change()
            
    def _on_pipette_toggled(self, checked):
        self.sig_pipette_toggled.emit(checked)
        if checked:
            self.setCursor(Qt.CrossCursor)
        else:
            self.unsetCursor()

    def _connect_signals(self):
        self.spn_start.valueChanged.connect(self._emit_change)
        self.spn_end.valueChanged.connect(self._emit_change) 
        self.spn_x.valueChanged.connect(self._emit_change)
        self.spn_y.valueChanged.connect(self._emit_change)
        self.spn_frame_w.valueChanged.connect(self._emit_change)
        self.spn_frame_h.valueChanged.connect(self._emit_change)
        self.spn_frame_rot.valueChanged.connect(self._emit_change)
        self.chk_lock_frame.toggled.connect(self._emit_change) 
        self.spn_scale.valueChanged.connect(self._emit_change)
        self.spn_rot.valueChanged.connect(self._emit_change)
        self.spn_opacity.valueChanged.connect(self._emit_change)
        self.spn_sf_l.valueChanged.connect(self._emit_change)
        self.spn_sf_r.valueChanged.connect(self._emit_change)
        # [MODIFIKASI] Connect 4 sinyal Feather
        self.spn_f_l.valueChanged.connect(self._emit_change)
        self.spn_f_r.valueChanged.connect(self._emit_change)
        self.spn_f_t.valueChanged.connect(self._emit_change)
        self.spn_f_b.valueChanged.connect(self._emit_change)
        
        self.slider_bright.valueChanged.connect(self._emit_change)
        self.slider_contrast.valueChanged.connect(self._emit_change)
        self.slider_sat.valueChanged.connect(self._emit_change)
        self.slider_hue.valueChanged.connect(self._emit_change)
        self.spn_sim.valueChanged.connect(self._emit_change)
        self.spn_smooth.valueChanged.connect(self._emit_change)
        self.slider_spill_r.valueChanged.connect(self._emit_change)
        self.slider_spill_g.valueChanged.connect(self._emit_change)
        self.slider_spill_b.valueChanged.connect(self._emit_change)

    def _emit_change(self):
        data = {
            "start_time": self.spn_start.value(),
            "end_time": self.spn_end.value(),
            "x": self.spn_x.value(), "y": self.spn_y.value(),
            "frame_w": self.spn_frame_w.value(), "frame_h": self.spn_frame_h.value(),
            "frame_rot": self.spn_frame_rot.value(), "lock": self.chk_lock_frame.isChecked(),
            "scale": self.spn_scale.value(), "rot": self.spn_rot.value(), "opacity": self.spn_opacity.value(),
            "sf_l": self.spn_sf_l.value(), "sf_r": self.spn_sf_r.value(),
            # [MODIFIKASI] Kirim 4 data feather
            "f_l": self.spn_f_l.value(),
            "f_r": self.spn_f_r.value(),
            "f_t": self.spn_f_t.value(),
            "f_b": self.spn_f_b.value(),
            
            "bright": self.slider_bright.value(), "contrast": self.slider_contrast.value(),
            "sat": self.slider_sat.value(), "hue": self.slider_hue.value(),
            "chroma_key": self.chroma_color_hex, "similarity": self.spn_sim.value(),
            "smoothness": self.spn_smooth.value(),
            "spill_r": self.slider_spill_r.value(), "spill_g": self.slider_spill_g.value(), "spill_b": self.slider_spill_b.value()
        }
        self.sig_media_changed.emit(data)

    def set_values(self, data):
        self.blockSignals(True)
        is_bg = data.get("is_bg", False)
        
        # 1. Atur Group Video (sudah ada sebelumnya)
        self.group_video.setEnabled(not is_bg)
        self.group_video.setTitle("VIDEO ATTRIBUTES (DISABLED FOR BG)" if is_bg else "CLIP ATTRIBUTES")
        
        # --- [PERBAIKAN DIMULAI] ---
        # 2. Atur Group Frame (Matikan total jika ini Background)
        self.group_frame.setEnabled(not is_bg)
        self.group_frame.setTitle("FRAME (DISABLED FOR BG)" if is_bg else "FRAME / CONTAINER")

        if "start_time" in data: self.spn_start.setValue(float(data["start_time"]))
        if "end_time" in data and data["end_time"] is not None: self.spn_end.setValue(float(data["end_time"]))
        else: s = self.spn_start.value(); self.spn_end.setValue(s + 5.0)
            
        # HANYA update nilai Frame jika BUKAN Background
        if not is_bg:
            if "x" in data: self.spn_x.setValue(data["x"])
            if "y" in data: self.spn_y.setValue(data["y"])
            if "frame_w" in data: self.spn_frame_w.setValue(data["frame_w"])
            if "frame_h" in data: self.spn_frame_h.setValue(data["frame_h"])
            if "frame_rot" in data: self.spn_frame_rot.setValue(data["frame_rot"])
            if "lock" in data: self.chk_lock_frame.setChecked(data["lock"])
        # --- [PERBAIKAN SELESAI] ---

        if "scale" in data: self.spn_scale.setValue(data["scale"])
        if "rot" in data: self.spn_rot.setValue(data["rot"])
        if "opacity" in data: self.spn_opacity.setValue(data["opacity"])
        if "sf_l" in data: self.spn_sf_l.setValue(data["sf_l"])
        if "sf_r" in data: self.spn_sf_r.setValue(data["sf_r"])
        
        # [MODIFIKASI] Set 4 data feather
        if "f_l" in data: self.spn_f_l.setValue(data["f_l"])
        if "f_r" in data: self.spn_f_r.setValue(data["f_r"])
        if "f_t" in data: self.spn_f_t.setValue(data["f_t"])
        if "f_b" in data: self.spn_f_b.setValue(data["f_b"])
        
        if "bright" in data: self.slider_bright.setValue(data["bright"])
        if "contrast" in data: self.slider_contrast.setValue(data["contrast"])
        if "sat" in data: self.slider_sat.setValue(data["sat"])
        if "hue" in data: self.slider_hue.setValue(data["hue"])
        
        if "chroma_key" in data:
            self.chroma_color_hex = data["chroma_key"]
            self.btn_pick_color.setStyleSheet(f"background-color: {self.chroma_color_hex}; color: black; font-weight: bold; border-radius: 3px; padding: 4px;")
        if "similarity" in data: self.spn_sim.setValue(data["similarity"])
        if "smoothness" in data: self.spn_smooth.setValue(data["smoothness"])
        
        if "spill_r" in data: self.slider_spill_r.setValue(data["spill_r"])
        if "spill_g" in data: self.slider_spill_g.setValue(data["spill_g"])
        if "spill_b" in data: self.slider_spill_b.setValue(data["spill_b"])
        
        self.blockSignals(False)