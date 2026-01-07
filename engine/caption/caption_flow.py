# engine/caption/caption_flow.py
import os
import subprocess
import tempfile

from engine.caption.assemblyai import assembly_upload, assembly_transcribe
from engine.caption.ass_builder import make_ass_from_words
from engine.caption.subtitle_renderer import burn_subtitle
from engine.caption.lang_detect import detect_language


def extract_audio(video_path, wav_path):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        wav_path
    ], check=True)


def apply_caption(
    video_path: str,
    output_path: str,
    preset: str = "karaoke"
):
    """
    Apply auto caption to video.
    preset: karaoke | chunk | netflix
    """

    if preset == "karaoke":
        words_per_event = 1
    elif preset == "chunk":
        words_per_event = 3
    else:
        words_per_event = 2

    with tempfile.TemporaryDirectory() as tmp:
        tmp_audio = os.path.join(tmp, "audio.wav")
        tmp_ass = os.path.join(tmp, "caption.ass")

        extract_audio(video_path, tmp_audio)

        lang = detect_language(tmp_audio)
        if lang not in ("id", "en"):
            lang = "id"

        upload_url = assembly_upload(tmp_audio)
        words = assembly_transcribe(upload_url, language_code=lang)

        ass_text = make_ass_from_words(
            words,
            words_per_event=words_per_event
        )

        with open(tmp_ass, "w", encoding="utf-8") as f:
            f.write(ass_text)

        burn_subtitle(video_path, tmp_ass, output_path)
