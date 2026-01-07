# engine/caption/lang_detect.py

_model = None

def detect_language(audio_path):
    """
    Deteksi bahasa audio pakai Whisper.
    WAJIB dipanggil sebelum AssemblyAI,
    agar language_code tidak salah aksen.
    """
    global _model

    try:
        import whisper
    except Exception as e:
        raise RuntimeError(
            f"Whisper gagal diimport. "
            f"Pastikan ffmpeg & whisper terinstall dengan benar.\n{e}"
        )

    if _model is None:
        try:
            _model = whisper.load_model("tiny")
        except Exception as e:
            raise RuntimeError(
                f"Gagal load Whisper model.\n{e}"
            )

    try:
        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)

        mel = whisper.log_mel_spectrogram(audio).to(_model.device)
        _, probs = _model.detect_language(mel)

        lang = max(probs, key=probs.get)
        return lang
    except Exception as e:
        raise RuntimeError(
            f"Whisper error saat deteksi bahasa.\n{e}"
        )
