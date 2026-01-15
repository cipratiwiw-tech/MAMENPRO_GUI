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
        self.duration = float(duration)
        
        # 🛡️ SAFETY 1: Paksa Dimensi Genap (Wajib untuk codec H.264)
        w = int(width)
        h = int(height)
        self.canvas_w = w if w % 2 == 0 else w + 1
        self.canvas_h = h if h % 2 == 0 else h + 1
        
        self.audio_tracks = audio_tracks if audio_tracks else []
        self.is_stopped = False
        self.process = None

    def stop(self):
        self.is_stopped = True
        if self.process:
            self.process.kill()

    # 🛡️ SAFETY 2: Sanitasi Angka (Koma -> Titik) untuk Locale Indonesia
    def _fmt(self, val):
        return f"{float(val):.3f}".replace(',', '.')

    def _humanize_error(self, stderr):
        s = stderr.lower() if stderr else ""
        if "nothing was written" in s:
            return "Render Gagal: Pipeline output kosong (Cek durasi layer)."
        if "invalid argument" in s:
            return "FFmpeg Error -22: Kesalahan parameter filter."
        return f"FFmpeg Error:\n{stderr[-800:]}"

    def run(self):
        self.sig_progress.emit("🚀 Menyiapkan Render Engine...")
        
        # Durasi minimal 1 detik untuk safety
        safe_duration = max(1.0, self.duration)
        s_dur = self._fmt(safe_duration)
        
        inputs = []
        filter_complex = []
        temp_files = [] 
        
        # =========================================================================
        # 1. BASE VISUAL LAYER (Canvas Hitam)
        # =========================================================================
        # Force format RGBA agar kompatibel dengan overlay
        filter_complex.append(
            f"color=c=black:s={self.canvas_w}x{self.canvas_h}:r=30:d={s_dur},format=rgba[base_v]"
        )
        last_vid_node = "[base_v]"
        
        # =========================================================================
        # 2. PROSES VISUAL
        # =========================================================================
        current_input_idx = 0 
        
        try:
            # Urutkan layer dari bawah ke atas
            sorted_items = sorted(self.items, key=lambda x: x.get('z_value', 0))

            for idx, item in enumerate(sorted_items):
                if self.is_stopped: break

                is_text = item.get('is_text', False)
                file_path = item.get('path')
                
                # --- HANDLING INPUT ---
                # Gunakan Absolute Path untuk keamanan
                if is_text:
                    temp_img = f"temp_render_text_{idx}.png"
                    abs_temp_path = os.path.abspath(temp_img)
                    
                    if item.get('text_pixmap'):
                        item['text_pixmap'].save(abs_temp_path)
                        temp_files.append(abs_temp_path)
                        inputs.extend(['-loop', '1', '-t', s_dur, '-i', abs_temp_path])
                    else:
                        # Dummy fallback jika teks gagal
                        inputs.extend(['-f', 'lavfi', '-i', f"color=c=black@0:s=100x100:d={s_dur}"])
                else:
                    if not file_path or not os.path.exists(file_path): 
                        continue
                    
                    abs_path = os.path.abspath(file_path)
                    ext = os.path.splitext(abs_path)[1].lower()
                    image_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
                    
                    if ext in image_exts:
                        inputs.extend(['-loop', '1', '-t', s_dur, '-i', abs_path])
                    else:
                        inputs.extend(['-i', abs_path])

                curr_in_node = f"[{current_input_idx}:v]"
                current_input_idx += 1

                # --- TRANSFORMASI ---
                # 🛡️ SAFETY 3: Ukuran Minimal 2x2 (Mencegah scale=0 error)
                vis_w = max(2, int(item['visual_w']))
                vis_h = max(2, int(item['visual_h']))
                
                # Pastikan genap
                if vis_w % 2 != 0: vis_w += 1
                if vis_h % 2 != 0: vis_h += 1
                
                pos_x = item['x']; pos_y = item['y']
                rot = item.get('rot', 0); opacity = item.get('opacity', 100)
                blur_val = item.get('blur', 0); vig_val = item.get('vig', 0)

                scaled_node = f"[s{idx}]"
                out_node = f"[layer{idx}]"

                filters = []
                filters.append("setpts=PTS-STARTPTS") 
                filters.append(f"scale={vis_w}:{vis_h}:flags=lanczos")
                
                if blur_val > 0: 
                    filters.append(f"gblur=sigma={self._fmt(blur_val * 0.5)}")
                if vig_val > 0: 
                    angle = (vig_val / 100.0) * 0.5
                    filters.append(f"vignette=angle={self._fmt(angle)}")
                if rot != 0: 
                    filters.append(f"rotate={rot}*PI/180:ow=rotw(iw):oh=roth(ih):c=none")
                
                op_val = self._fmt(opacity / 100.0)
                filters.append(f"format=rgba,colorchannelmixer=aa={op_val}")
                
                filter_complex.append(f"{curr_in_node}{','.join(filters)}{scaled_node}")

                # --- OVERLAY ---
                start_t = float(item.get('start_time') or 0.0)
                end_t = float(item.get('end_time') or safe_duration)
                if end_t <= start_t: end_t = start_t + 0.1
                
                s_start = self._fmt(start_t)
                s_end = self._fmt(end_t)
                
                ox = f"{pos_x}-(w-iw)/2"
                oy = f"{pos_y}-(h-ih)/2"
                
                # 🛡️ SAFETY 4: ENABLE TANPA KUTIP
                # Hapus tanda kutip tunggal di 'between(...)' agar aman di Windows
                overlay_cmd = (
                    f"{last_vid_node}{scaled_node}overlay={ox}:{oy}:"
                    f"enable=between(t,{s_start},{s_end}):format=auto{out_node}"
                )
                filter_complex.append(overlay_cmd)
                last_vid_node = out_node

            if self.is_stopped: 
                self.sig_finished.emit(False, "Dibatalkan."); return

            # Final Video Format
            final_vid_label = "[vfinal]"
            filter_complex.append(f"{last_vid_node}format=yuv420p{final_vid_label}")

            # =========================================================================
            # 3. PROSES AUDIO (MODE STABIL)
            # =========================================================================
            
            audio_inputs = []
            
            # Ambil audio hanya dari file musik eksternal (Aman)
            for track in self.audio_tracks:
                if track and os.path.exists(track):
                    inputs.extend(['-i', track])
                    resampled_node = f"[a_in_{current_input_idx}]"
                    # Resample ke 44100Hz agar seragam
                    filter_complex.append(f"[{current_input_idx}:a]aresample=44100{resampled_node}")
                    audio_inputs.append(resampled_node)
                    current_input_idx += 1
            
            final_audio_label = None
            
            # Jika ada musik, mix jadi satu
            if len(audio_inputs) > 0:
                final_audio_label = "[aout]"
                count = len(audio_inputs)
                # Mix tanpa durasi limit (ikut video via -shortest nanti)
                filter_complex.append(
                    f"{''.join(audio_inputs)}amix=inputs={count}:dropout_transition=0{final_audio_label}"
                )
            
            # =========================================================================
            # 4. EKSEKUSI FFmpeg
            # =========================================================================
            
            full_filter_str = ";".join(filter_complex)
            
            cmd = ['ffmpeg', '-y']
            cmd.extend(inputs)
            cmd.extend(['-filter_complex', full_filter_str])
            
            # Map Video
            cmd.extend(['-map', final_vid_label])
            
            # Map Audio (Hanya jika ada)
            if final_audio_label:
                cmd.extend(['-map', final_audio_label])
                cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
            else:
                # 🛡️ SAFETY 5: Jika tidak ada audio, jangan map apa-apa (Video Only)
                # Ini mencegah crash karena stream kosong/anullsrc
                pass 
            
            cmd.extend([
                '-c:v', 'libx264', 
                '-preset', 'ultrafast', 
                '-crf', '23', 
                '-shortest', # Stop jika salah satu stream habis (biasanya video)
                self.output_path
            ])

            print(f"RUNNING FFmpeg: {' '.join(cmd)}")
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
                self.sig_finished.emit(False, self._humanize_error(stdout))

        except Exception as e: 
            self.sig_finished.emit(False, f"System Error: {str(e)}")
        finally:
            for tmp in temp_files:
                if os.path.exists(tmp):
                    try: os.remove(tmp)
                    except: pass