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
        self.process = None # [BARU] Simpan instance subprocess

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

        for item in sorted_items:
            # Cek stop sebelum menambah input (meski yang krusial adalah kill process)
            if self.is_stopped: break
            
            file_path = item['path']
            is_image = item.get('is_image', False) 
            
            if not file_path: continue
            file_path = file_path.replace("\\", "/")

            if not os.path.exists(file_path):
                print(f"[SKIP] File tidak ditemukan: {file_path}")
                continue

            # Loop image = Infinite Stream (Penyebab render tidak berhenti jika tanpa -t)
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

            rotation = item.get('rot', 0)
            opacity = item.get('opacity', 100) / 100.0
           

            sf_l = int(item.get('sf_l', 0))
            sf_r = int(item.get('sf_r', 0))
            
            # [MODIFIKASI]
            f_l = int(item.get('f_l', 0))
            f_r = int(item.get('f_r', 0))
            f_t = int(item.get('f_t', 0))
            f_b = int(item.get('f_b', 0))

            node_pts = f"[pts{input_idx}]"
            node_cropped = f"[crop{input_idx}]"
            node_feathered = f"[fth{input_idx}]"
            node_scaled = f"[sc{input_idx}]"
            
            # 1. SETPTS
            filter_parts.append(f"{current_in_label}setpts=PTS-STARTPTS+({start_t}/TB){node_pts}")
            last_processed = node_pts

            # 2. CROP
            if sf_l > 0 or sf_r > 0:
                filter_parts.append(
                    f"{last_processed}crop=iw-{sf_l}-{sf_r}:ih:{sf_l}:0{node_cropped}"
                )
                last_processed = node_cropped
            
            # 3. INDEPENDENT FEATHER (GEQ Filter)
            # Logika GEQ: Jika pixel berada di area feather, kurangi alpha-nya.
            # Rumus Alpha = 255 * min(1, JarakKiri/FL, JarakKanan/FR, JarakAtas/FT, JarakBawah/FB)
            if f_l > 0 or f_r > 0 or f_t > 0 or f_b > 0:
                # Kita ubah format ke RGBA dulu
                # Lalu gunakan geq untuk memanipulasi channel Alpha (a)
                # 'X' dan 'Y' adalah koordinat pixel saat ini. 'W' dan 'H' adalah lebar/tinggi gambar.
                
                # Buat string expression untuk GEQ
                # gt(A,B) artinya A > B ? 1 : 0
                alpha_expr = "255"
                
                # Factor Kiri: X / f_l
                if f_l > 0: alpha_expr = f"min({alpha_expr}, X/{f_l})"
                
                # Factor Kanan: (W-X) / f_r
                if f_r > 0: alpha_expr = f"min({alpha_expr}, (W-X)/{f_r})"
                
                # Factor Atas: Y / f_t
                if f_t > 0: alpha_expr = f"min({alpha_expr}, Y/{f_t})"
                
                # Factor Bawah: (H-Y) / f_b
                if f_b > 0: alpha_expr = f"min({alpha_expr}, (H-Y)/{f_b})"
                
                # Clamp max 1 (untuk normalisasi jika pake min(1,...)) -> tapi karena kita mulai dari 255 dan bagi,
                # kita perlu pastikan nilai tidak melebihi 255. min() sudah handle itu.
                # Namun X/f_l bisa > 1. Jadi kita harus min(1, ...) lalu kali 255.
                
                # REVISI RUMUS YANG LEBIH AMAN:
                # 255 * min(1, val1, val2, ...)
                
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

            # 4. OPACITY
            if opacity < 1.0:
                filter_parts.append(f"{last_processed}format=rgba,colorchannelmixer=aa={opacity}{node_opacity}")
                last_processed = node_opacity

            # 5. OVERLAY
            filter_parts.append(
                f"{last_out_label}{last_processed}overlay={pos_x}:{pos_y}:"
                f"enable='between(t,{start_t:.3f},{end_t:.3f})'{node_overlay}"
            )
            last_out_label = node_overlay

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
        
        # [SOLUSI UTAMA] Paksa berhenti sesuai durasi timeline!
        # Tanpa ini, gambar yang di-loop akan membuat render berjalan selamanya.
        cmd.extend(['-t', str(self.duration)])
        
        cmd.append(self.output_path)
        
        self._run_process(cmd)

    def _run_process(self, cmd):
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # [MODIFIKASI] Simpan ke self.process
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True,
                startupinfo=startupinfo,
                encoding='utf-8', errors='replace'
            )
            
            # Communicate akan block thread ini sampai selesai atau di-kill
            stdout, stderr = self.process.communicate()
            
            # Cek status berhenti
            if self.is_stopped:
                self.sig_finished.emit(False, "Render Stopped by User.")
            elif self.process.returncode == 0:
                self.sig_finished.emit(True, f"Render Selesai!\nSaved to: {self.output_path}")
            else:
                self.sig_finished.emit(False, f"Error FFmpeg:\n{stderr[-600:]}")
                print("FFMPEG LOG:", stderr)

        except Exception as e:
            if not self.is_stopped: # Jangan lapor error jika memang kita yang stop
                self.sig_finished.emit(False, str(e))