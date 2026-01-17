import subprocess
import platform
import signal

class FFmpegRenderer:
    def __init__(self, output_path, width, height, fps):
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.process = None

    def start_process(self):
        # ... (Command cmd sama seperti sebelumnya) ...
        cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{self.width}x{self.height}',
            '-pix_fmt', 'rgb24',
            '-r', str(self.fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-pix_fmt', 'yuv420p',
            self.output_path
        ]
        
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
                # Terjadi jika FFmpeg crash duluan (misal disk penuh)
                print("❌ Error: FFmpeg Pipe Broken!")
                self.close_process()
                raise Exception("Render Interrupted: FFmpeg process died unexpectedly.")

    def close_process(self):
        """Memastikan proses mati total (Kill Zombie)"""
        if self.process:
            # 1. Tutup Pintu Masuk
            if self.process.stdin:
                try:
                    self.process.stdin.close()
                except: pass

            # 2. Tunggu selesai baik-baik
            try:
                self.process.wait(timeout=2) # Tunggu max 2 detik
            except subprocess.TimeoutExpired:
                # 3. Kalau bandel, BUNUH PAKSA
                print("⚠️ FFmpeg not stopping, force killing...")
                self.process.kill() 
            
            self.process = None