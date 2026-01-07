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
        
        # Base Canvas
        filter_complex.append(f"color=c=black:s={self.canvas_w}x{self.canvas_h}:d={self.duration}[base]")
        last_vid_node = "[base]"
        
        current_input_idx = 0
        
        try:
            sorted_items = sorted(self.items, key=lambda x: x.get('z_value', 0))

            for idx, item in enumerate(sorted_items):
                if self.is_stopped: break

                is_bg = item.get('is_bg', False)
                is_text = item.get('is_text', False)
                file_path = item.get('path', "")
                
                if is_text:
                    temp_img = f"temp_render_text_{idx}.png"
                    if item.get('text_pixmap'):
                        item['text_pixmap'].save(temp_img)
                        temp_files.append(temp_img)
                        inputs.extend(['-loop', '1', '-t', str(self.duration), '-i', temp_img])
                    else:
                        inputs.extend(['-f', 'lavfi', '-i', f"color=c=black@0:s=100x100:d={self.duration}"])
                else:
                    inputs.extend(['-i', file_path])
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.gif']:
                        audio_map_indices.append(current_input_idx)

                curr_in_node = f"[{current_input_idx}:v]"
                current_input_idx += 1

                vis_w = item['visual_w']; vis_h = item['visual_h']
                pos_x = item['x']; pos_y = item['y']
                rot = item.get('rot', 0); opacity = item.get('opacity', 100)
                
                # Filter Effects
                blur_val = item.get('blur', 0)
                vig_val = item.get('vig', 0)

                scaled_node = f"[s{idx}]"
                out_node = f"[layer{idx}]"

                # Chain filter
                filters = [f"scale={vis_w}:{vis_h}:flags=lanczos"]
                
                # Blur (gblur sigma) - estimasi: 0-50 slider -> 0-50 sigma
                if blur_val > 0:
                    filters.append(f"gblur=sigma={blur_val}")
                
                # Vignette (PI/20 * val)
                if vig_val > 0:
                    # Vignette filter syntax: vignette=angle=PI/4
                    # Kita map 0-100 ke intensitas
                    rad = (vig_val / 100.0) * 1.5 # max sekitar 1.5 rad
                    filters.append(f"vignette=angle={rad}")

                # Rotate
                if rot != 0:
                    filters.append(f"rotate={rot}*PI/180:ow=rotw(iw):oh=roth(ih):c=none")
                
                # Opacity
                if opacity < 100:
                    filters.append(f"format=rgba,colorchannelmixer=aa={opacity/100.0}")
                
                filter_chain = ",".join(filters)
                filter_complex.append(f"{curr_in_node}{filter_chain}{scaled_node}")

                # Overlay
                start_t = item.get('start_time', 0)
                end_t = item.get('end_time', self.duration)
                overlay_cmd = (
                    f"{last_vid_node}{scaled_node}overlay={pos_x}:{pos_y}:"
                    f"enable='between(t,{start_t},{end_t})':format=auto{out_node}"
                )
                filter_complex.append(overlay_cmd)
                last_vid_node = out_node

            if self.is_stopped: self.sig_finished.emit(False, "Stopped by User"); return

            for track in self.audio_tracks:
                if os.path.exists(track):
                    inputs.extend(['-i', track])
                    audio_map_indices.append(current_input_idx)
                    current_input_idx += 1

            audio_out_node = None
            if len(audio_map_indices) > 0:
                mix_inputs = "".join([f"[{i}:a]" for i in audio_map_indices])
                filter_complex.append(f"{mix_inputs}amix=inputs={len(audio_map_indices)}:duration=longest[aout]")
                audio_out_node = "[aout]"
            
            full_filter_str = ";".join(filter_complex)
            cmd = ['ffmpeg', '-y']; cmd.extend(inputs); cmd.extend(['-filter_complex', full_filter_str])
            cmd.extend(['-map', last_vid_node])
            if audio_out_node: cmd.extend(['-map', audio_out_node]); cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
            
            cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', self.output_path])

            self.sig_progress.emit("⚙️ Menjalankan FFmpeg...")
            print(" ".join(cmd))

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, startupinfo=startupinfo, encoding='utf-8', errors='replace')
            stdout, stderr = self.process.communicate()
            
            if self.is_stopped: self.sig_finished.emit(False, "Render Stopped.")
            elif self.process.returncode == 0: self.sig_finished.emit(True, f"Render Selesai!\nSaved to: {self.output_path}")
            else: self.sig_finished.emit(False, f"FFmpeg Error:\n{stderr[-800:] if stderr else 'Unknown'}")

        except Exception as e: self.sig_finished.emit(False, str(e))
        finally:
            for tmp in temp_files:
                if os.path.exists(tmp):
                    try: os.remove(tmp)
                    except: pass