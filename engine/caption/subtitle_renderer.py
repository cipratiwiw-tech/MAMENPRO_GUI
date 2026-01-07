import subprocess

def burn_subtitle(video, ass_file, output):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video,
        "-vf", f"subtitles={ass_file}",
        "-c:a", "copy",
        output
    ], check=True)
