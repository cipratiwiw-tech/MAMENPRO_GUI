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
        self.process = None

    def stop(self):
        self.is_stopped = True
        if self.process:
            self.process.kill()

    def run(self):
        self.sig_progress.emit("🚀 Memulai Render Engine...")
        
        inputs = []
        filter_complex = []
        audio_map_indices = [] 
        temp_files = [] 
        
        # 1. Base Canvas (Dasar Hitam)
        filter_complex.append(f"color=c=black:s={self.canvas_w}x{self.canvas_h}:d={self.duration}[base]")
        last_vid_node = "[base]"
        
        current_input_idx = 0
        
        try:
            # Urutkan berdasarkan Z-Value agar urutan tumpukan benar
            sorted_items = sorted(self.items, key=lambda x: x.get('z_value', 0))

            for idx, item in enumerate(sorted_items):
                if self.is_stopped: break

                is_text = item.get('is_text', False)
                file_path = item.get('path') # Bisa berupa None untuk Teks
                
                # --- HANDLING INPUT ---
                if is_text:
                    temp_img = f"temp_render_text_{idx}.png"
                    if item.get('text_pixmap'):
                        item['text_pixmap'].save(temp_img)
                        temp_files.append(temp_img)
                        inputs.extend(['-loop', '1', '-t', str(self.duration), '-i', temp_img])
                    else:
                        # Fallback jika teks kosong
                        inputs.extend(['-f', 'lavfi', '-i', f"color=c=black@0:s=100x100:d={self.duration}"])
                else:
                    # FIX NoneType Error: Pastikan path ada sebelum diproses os.path
                    if not file_path:
                        continue
                        
                    inputs.extend(['-i', file_path])
                    
                    # Cek Ekstensi untuk menentukan apakah file mungkin punya audio
                    ext = os.path.splitext(file_path)[1].lower()
                    video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
                    # Jangan masukkan gambar ke daftar audio map untuk menghindari error -22
                    if ext in video_exts:
                        # Catatan: Ini masih berasumsi video punya audio. 
                        # Jika video 'bisu' menyebabkan error, hapus baris di bawah.
                        audio_map_indices.append(current_input_idx)

                curr_in_node = f"[{current_input_idx}:v]"
                current_input_idx += 1

                # --- PARAMETER TRANSFORMASI ---
                vis_w = item['visual_w']; vis_h = item['visual_h']
                pos_x = item['x']; pos_y = item['y']
                rot = item.get('rot', 0); opacity = item.get('opacity', 100)
                blur_val = item.get('blur', 0)
                vig_val = item.get('vig', 0)

                scaled_node = f"[s{idx}]"
                out_node = f"[layer{idx}]"

                # --- FILTER CHAIN (MENYAMAKAN PREVIEW) ---
                filters = []
                
                # Pastikan dimensi genap untuk libx264
                rw = vis_w if vis_w % 2 == 0 else vis_w + 1
                rh = vis_h if vis_h % 2 == 0 else vis_h + 1
                filters.append(f"scale={rw}:{rh}:flags=lanczos")
                
                if blur_val > 0:
                    filters.append(f"gblur=sigma={blur_val * 0.5}") # Normalisasi sigma
                
                if vig_val > 0:
                    rad = (vig_val / 100.0) * 0.5
                    filters.append(f"vignette=angle={rad}")

                if rot != 0:
                    # ow/oh rotw/roth agar pivot di tengah (mencegah crop)
                    filters.append(f"rotate={rot}*PI/180:ow=rotw(iw):oh=roth(ih):c=none")
                
                # Wajib RGBA agar area kosong hasil rotasi/transparansi tidak hitam
                filters.append(f"format=rgba,colorchannelmixer=aa={opacity/100.0}")
                
                filter_complex.append(f"{curr_in_node}{','.join(filters)}{scaled_node}")

                # --- OVERLAY (KOMPENSASI PIVOT CENTER) ---
                start_t = item.get('start_time', 0)
                end_t = item.get('end_time', self.duration)
                
                # Rumus agar posisi (X,Y) di render sama dengan titik tengah di Preview Qt
                overlay_x = f"{pos_x}-(w-iw)/2"
                overlay_y = f"{pos_y}-(h-ih)/2"
                
                overlay_cmd = (
                    f"{last_vid_node}{scaled_node}overlay={overlay_x}:{overlay_y}:"
                    f"enable='between(t,{start_t},{end_t})':format=auto{out_node}"
                )
                filter_complex.append(overlay_cmd)
                last_vid_node = out_node

            if self.is_stopped: self.sig_finished.emit(False, "Render Dibatalkan."); return

            # --- AUDIO TRACKS (MUSIK LUAR) ---
            for track in self.audio_tracks:
                if track and os.path.exists(track):
                    inputs.extend(['-i', track])
                    audio_map_indices.append(current_input_idx)
                    current_input_idx += 1

            # --- MAPPING AUDIO ---
            audio_out_node = None
            if audio_map_indices:
                mix_inputs = "".join([f"[{i}:a]" for i in audio_map_indices])
                # Gunakan amix hanya jika ada audio, filter amix butuh minimal 1 stream valid
                filter_complex.append(f"{mix_inputs}amix=inputs={len(audio_map_indices)}:duration=longest[aout]")
                audio_out_node = "[aout]"
            
            # --- FINAL COMMAND ---
            full_filter_str = ";".join(filter_complex)
            cmd = ['ffmpeg', '-y']
            cmd.extend(inputs)
            cmd.extend(['-filter_complex', full_filter_str])
            cmd.extend(['-map', last_vid_node])
            
            if audio_out_node: 
                cmd.extend(['-map', audio_out_node])
                cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
            
            cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-crf', '18', self.output_path])

            self.sig_progress.emit("⚙️ Menjalankan FFmpeg...")
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                          universal_newlines=True, startupinfo=startupinfo, 
                                          encoding='utf-8', errors='replace')
            
            stdout, _ = self.process.communicate()
            
            if self.is_stopped: 
                self.sig_finished.emit(False, "Render Berhenti.")
            elif self.process.returncode == 0: 
                self.sig_finished.emit(True, f"Render Selesai!\nSaved to: {self.output_path}")
            else: 
                # Tangkap log error terakhir jika gagal
                self.sig_finished.emit(False, f"FFmpeg Error:\n{stdout[-500:]}")

        except Exception as e: 
            self.sig_finished.emit(False, f"Terjadi Kesalahan: {str(e)}")
        finally:
            for tmp in temp_files:
                if os.path.exists(tmp):
                    try: os.remove(tmp)
                    except: pass