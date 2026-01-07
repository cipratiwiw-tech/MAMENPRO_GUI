import subprocess
import os
import shutil
from PySide6.QtCore import QThread, Signal

class RenderWorker(QThread):
    sig_progress = Signal(str)
    sig_finished = Signal(bool, str)

    def __init__(self, items_data, output_path, duration, width=1080, height=1920, audio_tracks=None):
        super().__init__()
        self.items = items_data
        self.output_path = output_path
        self.duration = duration
        self.canvas_w = width
        self.canvas_h = height
        self.audio_tracks = audio_tracks if audio_tracks else []
        self.is_stopped = False

    def run(self):
        self.sig_progress.emit("🚀 Memulai Render Engine...")
        
        inputs = []
        filter_complex = []
        audio_map_indices = [] # Menyimpan index input yang memiliki audio
        temp_files = [] 
        
        # 1. Setup Base Canvas (Black Background)
        # Input ke-0 adalah virtual canvas
        filter_complex.append(f"color=c=black:s={self.canvas_w}x{self.canvas_h}:d={self.duration}[base]")
        last_vid_node = "[base]"
        
        current_input_idx = 0
        
        try:
            # Urutkan item berdasarkan Z-Value (Layering)
            sorted_items = sorted(self.items, key=lambda x: x.get('z_value', 0))

            for idx, item in enumerate(sorted_items):
                if self.is_stopped: break

                is_bg = item.get('is_bg', False)
                is_text = item.get('is_text', False)
                file_path = item.get('path', "")
                
                # --- A. INPUT HANDLING ---
                if is_text:
                    # Render Text Pixmap ke PNG
                    temp_img = f"temp_render_text_{idx}.png"
                    if item.get('text_pixmap'):
                        item['text_pixmap'].save(temp_img)
                        temp_files.append(temp_img)
                        # Loop image sepanjang durasi
                        inputs.extend(['-loop', '1', '-t', str(self.duration), '-i', temp_img])
                        # Text = Gambar = Tidak ada audio
                    else:
                        # Fallback dummy
                        inputs.extend(['-f', 'lavfi', '-i', f"color=c=black@0:s=100x100:d={self.duration}"])
                else:
                    # Video / Image File
                    inputs.extend(['-i', file_path])
                    
                    # Cek apakah ini video (punya audio) atau gambar
                    # Simplifikasi: Cek ekstensi
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.gif']:
                        # Asumsikan video punya audio
                        audio_map_indices.append(current_input_idx)

                # Node referensi input saat ini
                curr_in_node = f"[{current_input_idx}:v]"
                current_input_idx += 1

                # --- B. VISUAL FILTER HANDLING ---
                vis_w = item['visual_w']
                vis_h = item['visual_h']
                pos_x = item['x']
                pos_y = item['y']
                
                # Handling visual rotation (jika ada)
                rot = item.get('rot', 0)
                
                scaled_node = f"[s{idx}]"
                rotated_node = f"[r{idx}]" # Node baru untuk rotasi
                out_node = f"[layer{idx}]"

                # 1. Scale
                scale_filter = f"{curr_in_node}scale={vis_w}:{vis_h}:flags=lanczos"
                
                # 2. Rotate (FFmpeg rotate uses radians, or degree with PI)
                # Syntax: rotate=angle*PI/180:fillcolor=none
                if rot != 0:
                    # Chain scale -> rotate
                    filter_complex.append(f"{scale_filter},rotate={rot}*PI/180:ow=rotw(iw):oh=roth(ih):c=none{rotated_node}")
                    overlay_source = rotated_node
                    
                    # Koreksi posisi X/Y karena rotasi mengubah bounding box
                    # (Disederhanakan: Menggunakan pusat anchor yg sama di overlay)
                else:
                    # Hanya scale
                    filter_complex.append(f"{scale_filter}{scaled_node}")
                    overlay_source = scaled_node

                # 3. Overlay
                # enable='between...' digunakan untuk durasi item tertentu
                start_t = item.get('start_time', 0)
                end_t = item.get('end_time', self.duration)
                
                # Overlay logic
                overlay_cmd = (
                    f"{last_vid_node}{overlay_source}overlay={pos_x}:{pos_y}:"
                    f"enable='between(t,{start_t},{end_t})':format=auto{out_node}"
                )
                filter_complex.append(overlay_cmd)
                
                last_vid_node = out_node

            # --- C. AUDIO TRACKS EXTERNAL ---
            for track in self.audio_tracks:
                if os.path.exists(track):
                    inputs.extend(['-i', track])
                    audio_map_indices.append(current_input_idx)
                    current_input_idx += 1

            # --- D. AUDIO MIXING ---
            audio_out_node = None
            if len(audio_map_indices) > 0:
                # Gabungkan semua stream audio
                mix_inputs = "".join([f"[{i}:a]" for i in audio_map_indices])
                # Filter amix
                filter_complex.append(f"{mix_inputs}amix=inputs={len(audio_map_indices)}:duration=longest[aout]")
                audio_out_node = "[aout]"
            
            # --- E. KONSTRUKSI COMMAND ---
            full_filter_str = ";".join(filter_complex)
            
            cmd = ['ffmpeg', '-y']
            cmd.extend(inputs)
            cmd.extend(['-filter_complex', full_filter_str])
            
            # Map Video Akhir
            cmd.extend(['-map', last_vid_node])
            
            # Map Audio Akhir (Jika ada)
            if audio_out_node:
                cmd.extend(['-map', audio_out_node])
                cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
            
            # Encoding Video
            cmd.extend([
                '-c:v', 'libx264', 
                '-preset', 'ultrafast', # Gunakan medium/fast untuk kualitas lebih baik
                '-pix_fmt', 'yuv420p',  # Wajib untuk kompatibilitas player
                self.output_path
            ])

            self.sig_progress.emit("⚙️ Menjalankan FFmpeg...")
            print(" ".join(cmd)) # Debugging Command

            # Startup info untuk menyembunyikan console di Windows
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
                encoding='utf-8', 
                errors='replace'
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.sig_finished.emit(True, f"Render Selesai!\nSaved to: {self.output_path}")
            else:
                # Ambil 500 karakter terakhir error log
                err_msg = stderr[-800:] if stderr else "Unknown Error"
                self.sig_finished.emit(False, f"FFmpeg Error:\n{err_msg}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.sig_finished.emit(False, str(e))
        
        finally:
            # Bersihkan file temp
            for tmp in temp_files:
                if os.path.exists(tmp):
                    try: os.remove(tmp)
                    except: pass