import subprocess
import os
from PySide6.QtCore import QThread, Signal

class RenderWorker(QThread):
    sig_progress = Signal(str)
    sig_finished = Signal(bool, str)

    # [PERBAIKAN] Menambahkan parameter 'audio_tracks' di akhir
    def __init__(self, items_data, output_path, duration, width=1080, height=1920, audio_tracks=None):
        super().__init__()
        self.items = items_data
        self.output_path = output_path
        self.duration = duration
        self.canvas_w = width
        self.canvas_h = height
        # Simpan list audio (default list kosong jika None)
        self.audio_tracks = audio_tracks if audio_tracks is not None else []

    def run(self):
        self.sig_progress.emit("🚀 Memulai Render Engine...")

        # 1. SETUP CANVAS
        inputs = []
        filter_parts = []
        
        # Base Canvas Hitam [base]
        filter_parts.append(f"color=c=black:s={self.canvas_w}x{self.canvas_h}:d={self.duration}[base]")
        last_out_label = "[base]"
        
        # Urutkan berdasarkan Z-Value (Background Z=0, Frame Z=1, dst)
        sorted_items = sorted(self.items, key=lambda x: x['z_value'])

        # --- A. VIDEO LAYERS PROCESSING ---
        for idx, item in enumerate(sorted_items):
            file_path = item['path']
            is_bg = item['is_bg']
            
            inputs.extend(['-i', file_path])
            
            # Param
            vis_w = item['visual_w']
            vis_h = item['visual_h']
            pos_x = item['x']
            pos_y = item['y']
            start_t = item.get('start_time', 0)
            end_t = item.get('end_time', self.duration)

            # Labels
            in_node = f"[{idx}:v]"
            scaled_node = f"[s{idx}]"
            out_node = f"[layer{idx}]"

            # --- LOGIKA BACKGROUND ---
            if is_bg:
                filter_parts.append(f"{in_node}scale={vis_w}:{vis_h}:flags=lanczos{scaled_node}")
                filter_parts.append(
                    f"{last_out_label}{scaled_node}overlay={pos_x}:{pos_y}:"
                    f"enable='between(t,{start_t},{end_t})'{out_node}"
                )

            # --- LOGIKA FRAME (KOTAK) ---
            else:
                frm_w = item['frame_w']
                frm_h = item['frame_h']
                padded_node = f"[p{idx}]"
                cropped_node = f"[c{idx}]"

                # 1. Scale
                filter_parts.append(f"{in_node}scale={vis_w}:{vis_h}:flags=lanczos{scaled_node}")
                
                # 2. Pad (Safety Net)
                safe_w = max(vis_w, frm_w)
                safe_h = max(vis_h, frm_h)
                pad_x = (safe_w - vis_w) // 2
                pad_y = (safe_h - vis_h) // 2
                
                filter_parts.append(
                    f"{scaled_node}pad={safe_w}:{safe_h}:{pad_x}:{pad_y}:color=black@0{padded_node}"
                )
                
                # 3. Crop (Potong Sesuai Ukuran Frame)
                crop_x = (safe_w - frm_w) // 2
                crop_y = (safe_h - frm_h) // 2
                
                filter_parts.append(
                    f"{padded_node}crop={frm_w}:{frm_h}:{crop_x}:{crop_y}{cropped_node}"
                )
                
                # 4. Overlay
                filter_parts.append(
                    f"{last_out_label}{cropped_node}overlay={pos_x}:{pos_y}:"
                    f"enable='between(t,{start_t},{end_t})'{out_node}"
                )
            
            last_out_label = out_node

        # --- B. AUDIO INPUT HANDLING ---
        # [PERBAIKAN] Masukkan audio ke input ffmpeg agar tidak hilang
        num_video_inputs = len(sorted_items)
        audio_maps = []
        
        for i, audio_path in enumerate(self.audio_tracks):
            inputs.extend(['-i', audio_path])
            # Mapping index audio: dimulai setelah input video terakhir
            # Format: [index_input:a]
            audio_index = num_video_inputs + i
            audio_maps.append(f"{audio_index}:a")

        # Finishing Filter Complex
        full_filter = ";".join(filter_parts)
        
        cmd = ['ffmpeg', '-y']
        cmd.extend(inputs)
        cmd.extend(['-filter_complex', full_filter])
        
        # Map Video Stream dari filter terakhir
        cmd.extend(['-map', last_out_label])
        
        # [PERBAIKAN] Map Audio Streams (Simple Mix / First Track)
        # Jika ada audio, kita map track pertama dulu untuk mencegah silent
        # (Untuk mixing multiple audio yang sempurna butuh filter 'amix', 
        # tapi ini cukup untuk menghindari crash dan memasukkan suara utama)
        if audio_maps:
            cmd.extend(['-map', audio_maps[0]]) 
            cmd.extend(['-c:a', 'aac']) # Encode audio ke AAC
            
        cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p'])
        cmd.append(self.output_path)

        self.sig_progress.emit(f"⚙️ FFmpeg Process...")
        
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
                startupinfo=startupinfo
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.sig_finished.emit(True, f"Render Selesai: {self.output_path}")
            else:
                err_msg = stderr[-1000:] if stderr else "Unknown Error"
                self.sig_finished.emit(False, f"Error FFmpeg:\n{err_msg}")
                
        except Exception as e:
            self.sig_finished.emit(False, str(e))