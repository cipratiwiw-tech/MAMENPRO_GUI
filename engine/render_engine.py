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
        
        # 🛡️ SAFETY 1: Dimensi WAJIB Genap (Aturan Codec H.264)
        self.canvas_w = int(width) if int(width) % 2 == 0 else int(width) + 1
        self.canvas_h = int(height) if int(height) % 2 == 0 else int(height) + 1
        
        self.audio_tracks = audio_tracks if audio_tracks else []
        self.is_stopped = False
        self.process = None

    def stop(self):
        self.is_stopped = True
        if self.process:
            self.process.kill()

    def run(self):
        self.sig_progress.emit("🚀 Memulai Render (Internal Generator Mode)...")
        
        # Durasi minimal 1 detik untuk mencegah crash
        safe_duration = max(1.0, self.duration)
        
        inputs = []
        filter_complex = []
        
        # =========================================================================
        # 1. GENERATOR STREAM (DI DALAM FILTER, BUKAN INPUT)
        # =========================================================================
        # Ini teknik paling aman. Stream dibuat oleh filter graph, jadi labelnya pasti ada.
        
        # [base_v] = Canvas Hitam
        filter_complex.append(
            f"color=c=black:s={self.canvas_w}x{self.canvas_h}:r=30:d={safe_duration:.3f}[base_v]"
        )
        
        # [base_a] = Audio Hening (Stereo, 44.1kHz)
        filter_complex.append(
            f"anullsrc=channel_layout=stereo:sample_rate=44100:d={safe_duration:.3f}[base_a]"
        )
        
        last_vid_node = "[base_v]"
        
        # =========================================================================
        # 2. PROSES VISUAL
        # =========================================================================
        current_input_idx = 0 # Kita mulai dari 0 karena base tidak pakai input eksternal
        temp_files = [] 
        
        try:
            sorted_items = sorted(self.items, key=lambda x: x.get('z_value', 0))

            for idx, item in enumerate(sorted_items):
                if self.is_stopped: break

                is_text = item.get('is_text', False)
                file_path = item.get('path') 
                
                # --- HANDLING INPUT ---
                if is_text:
                    temp_img = f"temp_render_text_{idx}.png"
                    if item.get('text_pixmap'):
                        item['text_pixmap'].save(temp_img)
                        temp_files.append(temp_img)
                        inputs.extend(['-loop', '1', '-t', f"{safe_duration:.3f}", '-i', temp_img])
                    else:
                        inputs.extend(['-f', 'lavfi', '-i', f"color=c=black@0:s=100x100:d={safe_duration:.3f}"])
                else:
                    if not file_path or not os.path.exists(file_path): 
                        continue
                    
                    ext = os.path.splitext(file_path)[1].lower()
                    image_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
                    
                    if ext in image_exts:
                        # Image loop
                        inputs.extend(['-loop', '1', '-t', f"{safe_duration:.3f}", '-i', file_path])
                    else:
                        # Video normal
                        inputs.extend(['-i', file_path])

                curr_in_node = f"[{current_input_idx}:v]"
                current_input_idx += 1

                # --- TRANSFORMASI ---
                vis_w = item['visual_w']; vis_h = item['visual_h']
                pos_x = item['x']; pos_y = item['y']
                rot = item.get('rot', 0); opacity = item.get('opacity', 100)
                blur_val = item.get('blur', 0); vig_val = item.get('vig', 0)

                scaled_node = f"[s{idx}]"
                out_node = f"[layer{idx}]"

                filters = []
                filters.append("setpts=PTS-STARTPTS") # Reset timestamp
                
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
                
                if end_t <= start_t: end_t = start_t + 0.1
                
                overlay_cmd = (
                    f"{last_vid_node}{scaled_node}overlay={pos_x}-(w-iw)/2:{pos_y}-(h-ih)/2:"
                    f"enable='between(t,{start_t:.3f},{end_t:.3f})':format=auto{out_node}"
                )
                filter_complex.append(overlay_cmd)
                last_vid_node = out_node

            if self.is_stopped: 
                self.sig_finished.emit(False, "Render Dibatalkan."); return

            # Format Final YUV420P
            final_vid_label = "[vfinal]"
            filter_complex.append(f"{last_vid_node}format=yuv420p{final_vid_label}")

            # =========================================================================
            # 3. PROSES AUDIO (ANTI ERROR)
            # =========================================================================
            
            # Kita mulai dengan base silent yang SUDAH dibuat di filter_complex [base_a]
            audio_mix_inputs = ["[base_a]"]
            
            # Tambahkan musik eksternal (Input File)
            for track in self.audio_tracks:
                if track and os.path.exists(track):
                    inputs.extend(['-i', track])
                    audio_mix_inputs.append(f"[{current_input_idx}:a]")
                    current_input_idx += 1
            
            final_audio_label = "[afinal]"
            
            # Jika ada musik, mix dengan base. Jika tidak, pass-through base.
            if len(audio_mix_inputs) > 1:
                # Mix semua jadi satu
                count = len(audio_mix_inputs)
                # dropout_transition=0 mencegah volume naik turun saat transisi
                mix_cmd = f"{''.join(audio_mix_inputs)}amix=inputs={count}:duration=first:dropout_transition=0{final_audio_label}"
                filter_complex.append(mix_cmd)
            else:
                # Hanya ada silence, beri label baru agar map konsisten
                filter_complex.append(f"[base_a]anull{final_audio_label}") # Dummy filter untuk rename label

            # =========================================================================
            # 4. FINAL COMMAND
            # =========================================================================
            
            full_filter_str = ";".join(filter_complex)
            
            cmd = ['ffmpeg', '-y']
            cmd.extend(inputs)
            cmd.extend(['-filter_complex', full_filter_str])
            
            # Map Output Labels
            cmd.extend(['-map', final_vid_label])
            cmd.extend(['-map', final_audio_label])
            
            # Encoder Settings
            cmd.extend([
                '-c:v', 'libx264', 
                '-preset', 'ultrafast', 
                '-crf', '23', 
                '-c:a', 'aac', 
                '-b:a', '192k',
                '-shortest', # Berhenti jika stream terpendek habis (biasanya video krn durasi fix)
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
                self.sig_finished.emit(False, f"FFmpeg Error Log:\n{stdout[-1000:]}")

        except Exception as e: 
            self.sig_finished.emit(False, f"System Error: {str(e)}")
        finally:
            for tmp in temp_files:
                if os.path.exists(tmp):
                    try: os.remove(tmp)
                    except: pass