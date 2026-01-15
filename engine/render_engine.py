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
        
        # 🛡️ SAFETY 1: Dimensi Genap (Wajib untuk x264)
        self.canvas_w = int(width) if int(width) % 2 == 0 else int(width) + 1
        self.canvas_h = int(height) if int(height) % 2 == 0 else int(height) + 1
        
        self.audio_tracks = audio_tracks if audio_tracks else []
        self.is_stopped = False
        self.process = None

    def stop(self):
        self.is_stopped = True
        if self.process:
            self.process.kill()

    def _humanize_error(self, stderr):
        s = stderr.lower() if stderr else ""
        if "nothing was written" in s:
            return "Render Gagal: Pipeline tidak menghasilkan data.\nCoba restart aplikasi atau cek ukuran layer."
        if "invalid argument" in s:
            return "FFmpeg Error -22: Parameter filter salah.\nKemungkinan masalah dimensi ganjil atau durasi layer."
        return f"FFmpeg Error:\n{stderr[-800:] if stderr else 'Unknown Error'}"

    def run(self):
        self.sig_progress.emit("🚀 Memulai Render Engine...")
        
        inputs = []
        filter_complex = []
        
        # 🛡️ SAFETY 2: Durasi Minimum 1 Detik
        safe_duration = max(1.0, self.duration)
        FPS = 30
        
        # =========================================================================
        # 1. BASE GENERATOR (VIDEO & AUDIO)
        # =========================================================================
        # Base Video: Hitam, 30fps, SAR 1:1, Format RGBA (biar match overlay)
        filter_complex.append(
            f"color=c=black:s={self.canvas_w}x{self.canvas_h}:r={FPS}:d={safe_duration:.3f},format=rgba[base]"
        )
        last_vid_node = "[base]"
        
        # Base Audio: Silent
        filter_complex.append(
            f"anullsrc=channel_layout=stereo:sample_rate=44100:d={safe_duration:.3f}[aud_base]"
        )
        
        # =========================================================================
        # 2. INPUT PROCESSING
        # =========================================================================
        current_input_idx = 0
        temp_files = [] 
        
        try:
            sorted_items = sorted(self.items, key=lambda x: x.get('z_value', 0))

            for idx, item in enumerate(sorted_items):
                if self.is_stopped: break

                is_text = item.get('is_text', False)
                file_path = item.get('path')
                
                # --- INPUT FLAGS ---
                # Gunakan -r 30 agar timebase input gambar sama dengan output
                if is_text:
                    temp_img = f"temp_render_text_{idx}.png"
                    if item.get('text_pixmap'):
                        item['text_pixmap'].save(temp_img)
                        temp_files.append(temp_img)
                        inputs.extend(['-loop', '1', '-r', str(FPS), '-t', f"{safe_duration:.3f}", '-i', temp_img])
                    else:
                        inputs.extend(['-f', 'lavfi', '-i', f"color=c=black@0:s=100x100:d={safe_duration:.3f}"])
                else:
                    if not file_path or not os.path.exists(file_path): 
                        continue
                    
                    ext = os.path.splitext(file_path)[1].lower()
                    image_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
                    
                    if ext in image_exts:
                        inputs.extend(['-loop', '1', '-r', str(FPS), '-t', f"{safe_duration:.3f}", '-i', file_path])
                    else:
                        inputs.extend(['-i', file_path])

                curr_in_node = f"[{current_input_idx}:v]"
                current_input_idx += 1

                # --- TRANSFORM ---
                vis_w = item['visual_w']; vis_h = item['visual_h']
                pos_x = item['x']; pos_y = item['y']
                rot = item.get('rot', 0); opacity = item.get('opacity', 100)
                blur_val = item.get('blur', 0); vig_val = item.get('vig', 0)

                scaled_node = f"[s{idx}]"
                out_node = f"[layer{idx}]"

                filters = []
                # Reset timestamp agar loop gambar mulai dari 0
                filters.append("setpts=PTS-STARTPTS")
                
                # Scale Genap
                rw = vis_w if vis_w % 2 == 0 else vis_w + 1
                rh = vis_h if vis_h % 2 == 0 else vis_h + 1
                filters.append(f"scale={rw}:{rh}:flags=lanczos")
                
                if blur_val > 0: filters.append(f"gblur=sigma={blur_val * 0.5}")
                if vig_val > 0: filters.append(f"vignette=angle={(vig_val / 100.0) * 0.5}")
                if rot != 0: filters.append(f"rotate={rot}*PI/180:ow=rotw(iw):oh=roth(ih):c=none")
                
                filters.append(f"format=rgba,colorchannelmixer=aa={opacity/100.0:.2f}")
                
                filter_complex.append(f"{curr_in_node}{','.join(filters)}{scaled_node}")

                # --- OVERLAY ---
                start_t = float(item.get('start_time') or 0.0)
                end_t = float(item.get('end_time') or safe_duration)
                
                # 🛡️ SAFETY 3: Cegah end <= start (crash enable filter)
                if end_t <= start_t: end_t = start_t + 0.1
                
                # 🛡️ SAFETY 4: Format float string (jangan pakai scientific notation)
                enable_expr = f"enable='between(t,{start_t:.3f},{end_t:.3f})'"
                
                overlay_cmd = (
                    f"{last_vid_node}{scaled_node}overlay={pos_x}-(w-iw)/2:{pos_y}-(h-ih)/2:"
                    f"{enable_expr}:format=auto{out_node}"
                )
                filter_complex.append(overlay_cmd)
                last_vid_node = out_node

            if self.is_stopped: 
                self.sig_finished.emit(False, "Dibatalkan user."); return

            # Convert ke YUV420P di akhir pipeline video
            final_vid = "[vfinal]"
            filter_complex.append(f"{last_vid_node}format=yuv420p{final_vid}")

            # =========================================================================
            # 3. AUDIO MIXING (LOGIKA ROBUST)
            # =========================================================================
            
            # Input Musik Eksternal
            audio_inputs = []
            for track in self.audio_tracks:
                if track and os.path.exists(track):
                    inputs.extend(['-i', track])
                    audio_inputs.append(f"[{current_input_idx}:a]")
                    current_input_idx += 1
            
            final_audio_node = "[aud_base]" # Default pakai silent
            
            # 🛡️ SAFETY 5: HANYA pakai amix jika ada > 1 audio source (Silent + Musik)
            # Jika hanya silent, JANGAN panggil amix (hemat resource & cegah bug)
            if len(audio_inputs) > 0:
                # Gabungkan Silent Base + Musik
                all_audios = ["[aud_base]"] + audio_inputs
                count = len(all_audios)
                # duration=first artinya durasi audio mengikuti [aud_base] (video duration)
                filter_complex.append(
                    f"{''.join(all_audios)}amix=inputs={count}:duration=first:dropout_transition=0[aout]"
                )
                final_audio_node = "[aout]"
            
            # =========================================================================
            # 4. EXECUTE
            # =========================================================================
            
            cmd = ['ffmpeg', '-y']
            cmd.extend(inputs)
            cmd.extend(['-filter_complex', ";".join(filter_complex)])
            
            cmd.extend(['-map', final_vid])      # Map Video Final
            cmd.extend(['-map', final_audio_node]) # Map Audio Final
            
            cmd.extend([
                '-c:v', 'libx264', 
                '-preset', 'ultrafast', 
                '-crf', '23', 
                '-c:a', 'aac', 
                '-b:a', '192k',
                '-shortest',
                self.output_path
            ])

            print(f"[FFMPEG CMD] {' '.join(cmd)}")
            
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