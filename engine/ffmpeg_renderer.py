import subprocess
import platform

class FFmpegRenderer:
    def __init__(self, output_path, width, height, fps):
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.process = None

    def start_process(self):
        # Command FFmpeg yang sinkron dengan QImage.Format_RGB888
        cmd = [
            'ffmpeg',
            '-y', # Overwrite output
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{self.width}x{self.height}', # Resolusi
            '-pix_fmt', 'rgb24', # HARUS SAMA dengan QImage format
            '-r', str(self.fps),
            '-i', '-', # Input dari Pipe
            '-c:v', 'libx264', # Codec Output
            '-preset', 'ultrafast', # Biar cepat (ganti medium buat kualitas)
            '-pix_fmt', 'yuv420p', # Format pixel standar player
            self.output_path
        ]
        
        # Windows: Hilangkan console window popup
        creation_flags = 0
        if platform.system() == "Windows":
            creation_flags = subprocess.CREATE_NO_WINDOW

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            creationflags=creation_flags
        )

    def write_frame(self, raw_bytes):
        if self.process:
            self.process.stdin.write(raw_bytes)

    def close_process(self):
        if self.process:
            if self.process.stdin:
                self.process.stdin.close()
            self.process.wait()
            self.process = None