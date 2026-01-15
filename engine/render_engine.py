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

    def stop(self):
        self.is_stopped = True

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
            if self.is_stopped: break
            
            file_path = item['path']
            is_image = item.get('is_image', False) 
            
            if not file_path: continue
            file_path = file_path.replace("\\", "/")

            if not os.path.exists(file_path):
                print(f"[SKIP] File tidak ditemukan: {file_path}")
                continue

            # [FIX CRITICAL] Loop hanya untuk GAMBAR STATIC
            if is_image:
                inputs.extend(['-loop', '1', '-i', file_path])
            else:
                # Video File: Jangan pakai -loop 1, itu error buat mp4
                # Opsional: Jika ingin video looping: inputs.extend(['-stream_loop', '-1', '-i', file_path])
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

            # 1. SETPTS (Sinkronisasi Waktu)
            filter_parts.append(f"{current_in_label}setpts=PTS-STARTPTS+({start_t}/TB){node_pts}")
            last_processed = node_pts

            # 2. SCALE & CROP (Agar tidak gepeng)
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
        
        # --- COMMAND ---
        if self.is_stopped: return

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
        cmd.append(self.output_path)
        
        self._run_process(cmd)

    def _run_process(self, cmd):
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True,
                startupinfo=startupinfo,
                encoding='utf-8', errors='replace'
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.sig_finished.emit(True, f"Render Selesai!\nSaved to: {self.output_path}")
            else:
                self.sig_finished.emit(False, f"Error FFmpeg:\n{stderr[-600:]}")
                print("FFMPEG LOG:", stderr)

        except Exception as e:
            self.sig_finished.emit(False, str(e))