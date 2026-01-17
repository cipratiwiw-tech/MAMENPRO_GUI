import subprocess
import platform
import signal
import os

class FFmpegRenderer:
    def __init__(self, output_path, width, height, fps):
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.process = None

    def start_process(self, audio_path=None, audio_delay_ms=0):
        # 1. Base Command (Video dari Pipe)
        cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{self.width}x{self.height}',
            '-pix_fmt', 'rgb24',
            '-r', str(self.fps),
            '-i', '-', # Input 0: Video Pipe
        ]

        # 2. Audio Injection Logic
        if audio_path and os.path.exists(audio_path):
            cmd.extend(['-i', audio_path]) # Input 1: Audio File
            
            # [UPDATE LOGIC]
            if audio_delay_ms > 0:
                # Jika ada delay, pakai filter adelay
                delay_str = f"{audio_delay_ms}|{audio_delay_ms}"
                cmd.extend([
                    '-filter_complex', f"[1:a]adelay={delay_str}[aud]",
                    '-map', '0:v',      # Video dari Pipe
                    '-map', '[aud]',    # Audio dari Filter
                ])
            else:
                # Jika TIDAK ada delay (mulai dari 0), langsung map raw stream
                # Ini lebih aman & kompatibel untuk semua versi FFmpeg
                cmd.extend([
                    '-map', '0:v',
                    '-map', '1:a' 
                ])
            
            # Audio Encoding Settings (Standard AAC)
            cmd.extend(['-c:a', 'aac', '-b:a', '192k', '-ac', '2']) # Paksa stereo
            
        else:
            # Silent Video
            cmd.extend(['-map', '0:v'])

        # 3. Output Settings
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-pix_fmt', 'yuv420p',
            '-shortest', # Stop jika salah satu stream habis
            self.output_path
        ])
        
        # Debug Command (Cek console kalau masih bisu)
        print(f"[FFMPEG CMD] {' '.join(cmd)}")

        creation_flags = 0
        if platform.system() == "Windows":
            creation_flags = subprocess.CREATE_NO_WINDOW

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            creationflags=creation_flags
        )

    def write_frame(self, raw_bytes):
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(raw_bytes)
            except BrokenPipeError:
                print("❌ Error: FFmpeg Pipe Broken!")
                self.close_process()

    def close_process(self):
        if self.process:
            if self.process.stdin:
                try: self.process.stdin.close()
                except: pass

            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                print("⚠️ FFmpeg force kill...")
                self.process.kill()
            
            self.process = None