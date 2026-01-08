import streamlit as st
import os
from logic import download_audio, transcribe_audio, detect_events

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="AI Video Transcription Analyzer",
    layout="wide"
)

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def format_timestamp(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def get_context_range(x_seconds: float, buffer_seconds: int):
    start = max(0, int(x_seconds - buffer_seconds))
    end = int(x_seconds + buffer_seconds)
    return format_timestamp(start), format_timestamp(end)

def get_video_id(url: str) -> str:
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    return ""

def mmss_to_seconds(mmss: str) -> int:
    m, s = mmss.split(":")
    return int(m) * 60 + int(s)

# --------------------------------------------------
# Session State
# --------------------------------------------------
if "current_video" not in st.session_state:
    st.session_state.current_video = None

if "results" not in st.session_state:
    st.session_state.results = None

# --------------------------------------------------
# UI Header
# --------------------------------------------------
st.title("🎧 AI Video Transcription Analyzer")
st.write(
    "Extract Question–Answer, Agreement, and Disagreement moments "
    "from YouTube videos using AI-based audio analysis."
)

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.header("Settings")

    youtube_url = st.text_input(
        "YouTube URL",
        placeholder="https://youtu.be/..."
    )

    buffer_seconds = st.slider(
        "Context buffer (seconds)",
        10, 30, 15
    )

    analyze_btn = st.button("🚀 Analyze Video")
    clear_btn = st.button("🧹 Clear State")

# --------------------------------------------------
# Clear State
# --------------------------------------------------
if clear_btn:
    st.session_state.current_video = None
    st.session_state.results = None
    st.experimental_rerun()

# --------------------------------------------------
# Analyze Video
# --------------------------------------------------
if analyze_btn and youtube_url:
    if st.session_state.current_video != youtube_url:
        st.session_state.current_video = youtube_url
        st.session_state.results = None

    with st.spinner("Downloading audio from YouTube..."):
        audio_path = download_audio(youtube_url)

    with st.spinner("Transcribing audio using Whisper..."):
        segments = transcribe_audio(audio_path)

    with st.spinner("Detecting conversational events..."):
        st.session_state.results = detect_events(segments)

    if audio_path and os.path.exists(audio_path):
        os.remove(audio_path)

    st.success("Analysis complete!")

# --------------------------------------------------
# Display Results
# --------------------------------------------------
if st.session_state.results:
    tabs = st.tabs(["❓ Q&A", "🤝 Agreement", "⚡ Disagreement"])

    def render_events(events, category):
        if not events:
            st.info("No moments detected.")
            return

        video_id = get_video_id(st.session_state.current_video)

        for idx, e in enumerate(events):
            # ------------------------------------------
            # Context Range (x - y -> x + y)
            # ------------------------------------------
            start_time, end_time = get_context_range(
                e["start"], buffer_seconds
            )

            st.markdown(
                f"**Event Context Range:** {start_time} → {end_time}"
            )
            st.write(e["text"])

            # ------------------------------------------
            # Play Clip Button (unique key!)
            # ------------------------------------------
            if st.button(
                f"▶️ Play Clip {idx+1}",
                key=f"play_{category}_{idx}"
            ):
                start_sec = mmss_to_seconds(start_time)

                embed_url = (
                    f"https://www.youtube.com/embed/{video_id}"
                    f"?start={start_sec}&autoplay=1"
                )

                st.video(embed_url)
                st.caption(
                    "▶️ Video starts at detected context range. "
                    "Playback duration is controlled by YouTube."
                )

            st.divider()

    with tabs[0]:
        render_events(st.session_state.results["qa"], "qa")

    with tabs[1]:
        render_events(st.session_state.results["agreement"], "agreement")

    with tabs[2]:
        render_events(st.session_state.results["disagreement"], "disagreement")
