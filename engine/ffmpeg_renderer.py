# engine/ffmpeg_renderer.py
import subprocess
import shutil
import os

class FFmpegRenderer:
    # [FIX] Wajib menerima 4 parameter ini
    def __init__(self, output_path, width, height, fps):
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.process = None

    def start_process(self, audio_path=None, audio_delay_ms=0):
        cmd = [
            'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
            '-s', f'{self.width}x{self.height}', '-pix_fmt', 'rgb24',
            '-r', str(self.fps), '-i', '-', 
        ]

        if audio_path and os.path.exists(audio_path):
            cmd.extend(['-i', audio_path])
            cmd.extend(['-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k', '-ac', '2'])
        else:
            cmd.extend(['-map', '0:v'])

        cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-shortest', self.output_path])
        print(f"[FFMPEG] {' '.join(cmd)}")

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # [FIX] stderr=None untuk mencegah macet buffer
        self.process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stderr=None, stdout=None, startupinfo=startupinfo
        )

    def write_frame(self, raw_data):
        if not self.process or not self.process.stdin: return
        if self.process.poll() is not None: return
        try: self.process.stdin.write(raw_data)
        except (BrokenPipeError, OSError): pass

    def close_process(self):
        if self.process:
            if self.process.stdin:
                try: self.process.stdin.close()
                except: pass
            try: self.process.wait(timeout=2)
            except: self.process.kill()
            self.process = None