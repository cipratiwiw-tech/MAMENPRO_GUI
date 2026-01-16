import os
import time
import requests
from dotenv import load_dotenv

# [FIX] Load .env secara spesifik dari folder engine/caption/
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(env_path)

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not ASSEMBLYAI_API_KEY:
    raise RuntimeError("ASSEMBLYAI_API_KEY tidak ditemukan di .env")

AIAI_UPLOAD = "https://api.assemblyai.com/v2/upload"
AIAI_TRANSCRIPT = "https://api.assemblyai.com/v2/transcript"

HEADERS = {
    "authorization": ASSEMBLYAI_API_KEY,
    "content-type": "application/json"
}


def assembly_upload(audio_path):
    headers = {"authorization": ASSEMBLYAI_API_KEY}
    with open(audio_path, "rb") as f:
        r = requests.post(AIAI_UPLOAD, headers=headers, data=f)
    r.raise_for_status()
    return r.json()["upload_url"]


def assembly_transcribe(upload_url, language_code="id"):
    """
    Transcribe audio via AssemblyAI (FULL REST).
    language_code: "id", "en", dll
    """

    # 1️⃣ Create transcript job
    payload = {
        "audio_url": upload_url,
        "language_code": language_code,   # 🔑 PAKSA BAHASA
        "punctuate": True,
        "format_text": True
    }

    r = requests.post(
        AIAI_TRANSCRIPT,
        headers=HEADERS,
        json=payload
    )
    r.raise_for_status()
    transcript_id = r.json()["id"]

    # 2️⃣ Poll sampai selesai
    while True:
        r = requests.get(
            f"{AIAI_TRANSCRIPT}/{transcript_id}",
            headers=HEADERS
        )
        r.raise_for_status()
        data = r.json()

        status = data["status"]
        if status == "completed":
            break
        if status == "error":
            raise RuntimeError(f"AssemblyAI error: {data['error']}")

        time.sleep(1.5)

    # 3️⃣ Ambil word timestamps
    words = []
    for w in data.get("words", []):
        words.append({
            "word": w["text"],
            "start": w["start"] / 1000.0,
            "end": w["end"] / 1000.0
        })

    return words
