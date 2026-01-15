# engine/caption/subtitle_renderer.py
import subprocess

def burn_subtitle(video, ass_file, output):
    # Menggunakan -map 0:a? agar audio hanya disalin jika ada
    # Menggunakan -c:a aac (re-encode) lebih aman daripada 'copy' untuk sinkronisasi
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video,
        "-vf", f"subtitles={ass_file}",
        "-map", "0:v",      # Ambil video stream 0
        "-map", "0:a?",     # Ambil audio stream 0 jika ada (?)
        "-c:v", "libx264",
        "-c:a", "aac",      # Re-encode ke aac
        "-shortest",        # Sesuaikan durasi
        output
    ], check=True)