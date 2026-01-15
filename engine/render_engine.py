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

            node_pts = f"[pts{input_idx}]"
            node_scaled = f"[sc{input_idx}]"
            node_rotated = f"[rt{input_idx}]"
            node_opacity = f"[op{input_idx}]"
            node_overlay = f"[lay{input_idx}]"

            # 1. SETPTS
            filter_parts.append(f"{current_in_label}setpts=PTS-STARTPTS+({start_t}/TB){node_pts}")
            last_processed = node_pts

            # 2. SCALE & CROP
            filter_parts.append(
                f"{last_processed}scale=w={vis_w}:h={vis_h}:force_original_aspect_ratio=increase,"
                f"crop={vis_w}:{vis_h}{node_scaled}"
            )
            last_processed = node_scaled

            # 3. ROTATE
            if rotation != 0:
                rad = rotation * (math.pi / 180)
                filter_parts.append(
                    f"{last_processed}rotate={rad}:ow='rotw({rad})':oh='roth({rad})':c=none{node_rotated}"
                )
                last_processed = node_rotated

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