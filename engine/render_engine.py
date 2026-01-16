import subprocess
import os
import math
from PySide6.QtCore import QThread, Signal

class RenderWorker(QThread):
    sig_progress = Signal(str)
    sig_finished = Signal(bool, str)

    def __init__(self, items_data, output_path, duration, width=1080, height=1920, audio_tracks=None):
        super().__init__()
        self.items = items_data
        self.output_path = output_path
        self.duration = float(duration)
        self.canvas_w = width
        self.canvas_h = height
        self.audio_tracks = audio_tracks if audio_tracks is not None else []
        self.is_stopped = False
        self.process = None # [BARU] Simpan instance subprocess.
        # Simpan path file subtitle .ass
        self.subtitle_file = subtitle_file
        
    def stop(self):
        """Dipanggil dari Controller saat tombol Stop diklik"""
        self.is_stopped = True
        if self.process:
            print("[RENDER ENGINE] Killing FFmpeg process...")
            try:
                self.process.kill() # Matikan paksa FFmpeg
            except Exception as e:
                print(f"Error killing process: {e}")

    def run(self):
        self.sig_progress.emit("🚀 Memulai Render Engine...")

        filter_parts = []
        inputs = []
        
        # [BASE LAYER] Canvas dasar Hitam
        filter_parts.append(f"color=c=black:s={self.canvas_w}x{self.canvas_h}:d={self.duration}[base]")
        last_out_label = "[base]"
        
        # Urutkan berdasarkan Z-Value
        sorted_items = sorted(self.items, key=lambda x: x['z_value'])
        
        input_idx = 0

        # --- LOOP PROCESS VISUAL ITEMS ---
        for item in sorted_items:
            # Cek stop
            if self.is_stopped: break
            
            file_path = item['path']
            is_image = item.get('is_image', False) 
            
            if not file_path: continue
            file_path = file_path.replace("\\", "/")

            if not os.path.exists(file_path):
                print(f"[SKIP] File tidak ditemukan: {file_path}")
                continue

            # Input logic
            if is_image:
                inputs.extend(['-loop', '1', '-i', file_path])
            else:
                inputs.extend(['-i', file_path])
                
            current_in_label = f"[{input_idx}:v]"
            input_idx += 1

            vis_w = int(item['visual_w'])
            vis_h = int(item['visual_h'])
            pos_x = int(item['x'])
            pos_y = int(item['y'])
            
            start_raw = item.get('start_time')
            end_raw = item.get('end_time')
            start_t = float(start_raw) if start_raw is not None else 0.0
            end_t = float(end_raw) if end_raw is not None else self.duration

            opacity = item.get('opacity', 100) / 100.0
            
            sf_l = int(item.get('sf_l', 0))
            sf_r = int(item.get('sf_r', 0))
            
            f_l = int(item.get('f_l', 0))
            f_r = int(item.get('f_r', 0))
            f_t = int(item.get('f_t', 0))
            f_b = int(item.get('f_b', 0))

            node_pts = f"[pts{input_idx}]"
            node_cropped = f"[crop{input_idx}]"
            node_feathered = f"[fth{input_idx}]"
            node_scaled = f"[sc{input_idx}]"
            
            node_opacity = f"[op{input_idx}]"
            node_overlay = f"[ov{input_idx}]"
            
            # 1. SETPTS
            filter_parts.append(f"{current_in_label}setpts=PTS-STARTPTS+({start_t}/TB){node_pts}")
            last_processed = node_pts

            # 2. CROP
            if sf_l > 0 or sf_r > 0:
                filter_parts.append(
                    f"{last_processed}crop=iw-{sf_l}-{sf_r}:ih:{sf_l}:0{node_cropped}"
                )
                last_processed = node_cropped
            
            # 3. FEATHER (GEQ Filter)
            if f_l > 0 or f_r > 0 or f_t > 0 or f_b > 0:
                terms = ["1"]
                if f_l > 0: terms.append(f"X/{f_l}")
                if f_r > 0: terms.append(f"(W-X)/{f_r}")
                if f_t > 0: terms.append(f"Y/{f_t}")
                if f_b > 0: terms.append(f"(H-Y)/{f_b}")
                
                min_expr = f"min({','.join(terms)})"
                geq_filter = f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='255*{min_expr}'"

                filter_parts.append(
                    f"{last_processed}format=rgba,{geq_filter}{node_feathered}"
                )
                last_processed = node_feathered

            # 4. SCALE
            filter_parts.append(
                f"{last_processed}scale=w={vis_w}:h={vis_h}:force_original_aspect_ratio=increase,"
                f"crop={vis_w}:{vis_h}{node_scaled}"
            )
            last_processed = node_scaled

            # 5. OPACITY
            if opacity < 1.0:
                filter_parts.append(f"{last_processed}format=rgba,colorchannelmixer=aa={opacity}{node_opacity}")
                last_processed = node_opacity

            # 6. OVERLAY
            filter_parts.append(
                f"{last_out_label}{last_processed}overlay={pos_x}:{pos_y}:"
                f"enable='between(t,{start_t:.3f},{end_t:.3f})'{node_overlay}"
            )
            last_out_label = node_overlay

        # --- [NEW] SUBTITLE PROCESSING ---
        # Menggunakan subtitle_file yang dikirim dari controller
        if self.subtitle_file and os.path.exists(self.subtitle_file):
            # Escape path untuk Windows (FFmpeg filter butuh escape khusus pada backslash dan colon)
            # Contoh: C:\Path -> C\:/Path
            sub_path_escaped = self.subtitle_file.replace("\\", "/").replace(":", "\\:")
            
            next_label = "[v_subbed]"
            
            # Pasang filter subtitles ke chain terakhir (last_out_label)
            # force_style='Fontname=Arial,PrimaryColour=&H00FFFFFF' bisa ditambahkan jika ingin override .ass
            filter_parts.append(f"{last_out_label}subtitles='{sub_path_escaped}'{next_label}")
            
            # Update output label terakhir menjadi video yang sudah ada subtitlenya
            last_out_label = next_label
            print(f"[RENDER] Subtitle burned: {self.subtitle_file}")

        # --- AUDIO ---
        audio_cmds = []
        if self.audio_tracks:
            for track in self.audio_tracks:
                track = track.replace("\\", "/")
                if os.path.exists(track):
                    inputs.extend(['-i', track])
                    audio_cmds.append(f"[{input_idx}:a]") 
                    input_idx += 1
        
        # --- COMMAND EXECUTION ---
        if self.is_stopped: 
            self.sig_finished.emit(False, "Render dihentikan sebelum mulai.")
            return

        full_filter = ";".join(filter_parts)
        
        cmd = ['ffmpeg', '-y']
        cmd.extend(inputs)
        cmd.extend(['-filter_complex', full_filter])
        cmd.extend(['-map', last_out_label])
        
        if len(audio_cmds) > 0:
            for ac in audio_cmds:
                cmd.extend(['-map', ac])
        
        cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p'])
        cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
        
        # Paksa berhenti sesuai durasi timeline
        cmd.extend(['-t', str(self.duration)])
        
        cmd.append(self.output_path)
        
        self._run_process(cmd)

    def _run_process(self, cmd):
        # Helper untuk menjalankan subprocess agar lebih rapi
        print(f"[CMD] {' '.join(cmd)}")
        try:
            # Gunakan startupinfo untuk menyembunyikan console window di Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True,
                startupinfo=startupinfo,
                encoding='utf-8', errors='ignore' # Tambahan encoding agar aman
            )
            
            # Baca output progress (opsional, bisa dikembangkan untuk progress bar)
            while True:
                line = self.process.stderr.readline()
                if not line and self.process.poll() is not None:
                    break
                if line:
                    # Print log ffmpeg (bisa difilter jika terlalu berisik)
                    # print(line.strip())
                    pass
            
            if self.process.returncode == 0:
                self.sig_finished.emit(True, "Render Selesai!")
            else:
                self.sig_finished.emit(False, "Render Gagal (FFmpeg Error)")
                
        except Exception as e:
            self.sig_finished.emit(False, f"Error System: {str(e)}")