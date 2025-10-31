import streamlit as st
from datetime import datetime

from controllers.voice_controller import VoiceService
from components.audio_player import audio_player

async def handle_voice_generation(voice_service, text, emotion):
    """Handle the voice generation process with proper error handling"""
    try:
        timestamp = datetime.now().strftime("%H%M%S")
        with st.spinner("Synthesizing voice..."):
            preview_path = voice_service.generate_speech(text, emotion)

        if preview_path:
            st.session_state.last_preview = {
                "path": preview_path,
                "text": text,
                "emotion": emotion,
                "time": datetime.now()
            }
            st.success("Preview generated!")
            return True
    except Exception as e:
        st.error(f"Generation failed: {str(e)}")
        return False


async def voice_page():
    st.title("🎙️ Voice Studio")

    # Initialize with loading state
    if 'voice_service' not in st.session_state:
        st.session_state.voice_service = VoiceService()
        st.session_state.voice_loading = True
        st.session_state.voice_error = None

    # Get reference to service
    voice_service = st.session_state.voice_service

    # Check initialization status
    if voice_service.is_initializing():
        with st.status("🚀 Initializing Voice Engine...", expanded=True) as status:
            st.write("Loading AI models (this may take 30-60 seconds)")
            st.write("You can continue using other features while this loads")

            # Check if initialization completed
            if voice_service.wait_for_init(timeout=1.0):
                status.update(label="Voice Engine Ready!", state="complete")
                st.balloons()  # Visual confirmation
                st.rerun()  # Force refresh to show UI
            else:
                st.spinner()
        return

    # Handle error state
    if voice_service.get_error():
        st.error(f"Voice initialization failed: {voice_service.get_error()}")
        st.warning("Voice features are currently unavailable")
        return

    # Main content when ready
    if voice_service.is_ready():
        # Clear any previous loading state
        if st.session_state.get('voice_loading', False):
            st.session_state.voice_loading = False
            st.rerun()

        await render_voice_ui(voice_service)

async def render_voice_ui(voice_service):
    """Render the actual voice UI once service is ready"""
    # Section 1: Voice Preview Generator
    with st.expander("🎚️ Voice Preview Lab", expanded=True):
        preview_col1, preview_col2 = st.columns([3, 1])

        with preview_col1:
            preview_text = st.text_area(
                "Enter text to vocalize",
                value='"Hello there! How can I help you today?"',
                height=100,
                key="voice_preview_text"
            )

        with preview_col2:
            emotion = st.selectbox(
                "Voice Style",
                options=voice_service.get_available_emotions(),
                index=1,  # Default to 'neutral'
                key="voice_preview_emotion"
            )

            if st.button("✨ Generate Preview",
                         use_container_width=True,
                         type="primary",
                         key="generate_preview"):
                if not preview_text.strip():
                    st.warning("Please enter some text")
                else:
                    # Handle the generation in a separate function
                    await handle_voice_generation(voice_service, preview_text, emotion)

    # Display the last generated preview
    if "last_preview" in st.session_state:
        st.subheader("Latest Preview")
        preview = st.session_state.last_preview

        with st.container(border=True):
            cols = st.columns([1, 4, 1])
            with cols[0]:
                st.markdown(f"**{preview['emotion'].capitalize()}**")
            with cols[1]:
                st.caption(preview['text'][:50] + "..." if len(preview['text']) > 50 else preview['text'])
            with cols[2]:
                st.caption(preview['time'].strftime("%H:%M:%S"))

            # Use our enhanced audio player
            audio_player(
                preview['path'],
                autoplay=True,
                downloadable=True,
                key=f"preview_{preview['time'].timestamp()}"
            )

    # Section 2: Voice Management (removed bot assignment)
    with st.expander("⚙️ Voice Profiles"):
        st.write("Available voice profiles:")
        for emotion in voice_service.get_available_emotions():
            st.write(f"- {emotion.capitalize()}")

        st.write("\nTo add new voice profiles, place reference audio files in:")

        # Get the config safely
        if hasattr(voice_service, 'config'):
            audio_ref_dir = voice_service.config.get("audio_ref_dir", "Unknown directory")
            st.code(str(audio_ref_dir))
        else:
            st.warning("Could not retrieve voice service configuration")
            st.code("Configuration not available")