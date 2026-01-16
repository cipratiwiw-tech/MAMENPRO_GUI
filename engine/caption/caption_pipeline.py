# engine/caption/caption_flow.py
import os
import subprocess
import tempfile
import av
from engine.caption.assemblyai import assembly_upload, assembly_transcribe
from engine.caption.ass_builder import make_ass_from_words
from engine.caption.subtitle_renderer import burn_subtitle
from engine.caption.lang_detect import detect_language
from engine.caption.assemblyai import assembly_upload, assembly_transcribe

# [TAMBAHKAN FUNGSI INI]
def get_transcript_data(video_path):
    """
    Hanya mengambil data kata dari audio tanpa merender video.
    Returns: List of dict {'word': 'Halo', 'start': 0.5, 'end': 1.0}
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_audio = os.path.join(tmp, "audio.wav")
        
        # 1. Ekstrak Audio
        if not extract_audio(video_path, tmp_audio):
            print("⚠️ Tidak ada audio.")
            return []

        # 2. Deteksi Bahasa
        lang = detect_language(tmp_audio)
        if lang not in ("id", "en"):
            lang = "id"

        # 3. Transcribe via AssemblyAI
        try:
            upload_url = assembly_upload(tmp_audio)
            words = assembly_transcribe(upload_url, language_code=lang)
            return words
        except Exception as e:
            print(f"Error Transcribe: {e}")
            return []
        
def extract_audio(video_path, wav_path):
    # Cek audio dulu sebelum diekstrak
    with av.open(video_path) as container:
        if len(container.streams.audio) == 0:
            return False # Tidak ada audio
            
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn", "-ac", "1", "-ar", "16000",
        wav_path
    ], check=True)
    return True


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
        
        # Cek apakah ekstraksi berhasil/audio tersedia
        if not extract_audio(video_path, tmp_audio):
            print("⚠️ Video tidak memiliki audio. Melewati pembuatan caption.")
            # Opsi: Copy video asli ke output_path jika tidak ingin error
            import shutil
            shutil.copy(video_path, output_path)
            return

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


