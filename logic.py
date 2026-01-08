import whisper
import yt_dlp
import os
import uuid

model = whisper.load_model("base")

def download_audio(youtube_url):
    uid = str(uuid.uuid4())
    output_template = f"audio_{uid}.%(ext)s"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    for file in os.listdir("."):
        if file.startswith(f"audio_{uid}") and file.endswith(".mp3"):
            return file

    raise FileNotFoundError("Audio download failed.")

def transcribe_audio(audio_path):
    result = model.transcribe(audio_path)
    return result["segments"]

def detect_events(segments):
    results = {"qa": [], "agreement": [], "disagreement": []}

    for seg in segments:
        text = seg["text"].lower()

        if "?" in text:
            results["qa"].append(seg)

        if any(w in text for w in ["yes", "exactly", "right", "agree"]):
            results["agreement"].append(seg)

        if any(w in text for w in ["no", "not true", "disagree", "but"]):
            results["disagreement"].append(seg)

    return results
