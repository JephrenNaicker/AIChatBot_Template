import streamlit as st
from controllers.voice_controller import VoiceService
from components.audio_player import audio_player
from datetime import datetime
import asyncio


def handle_voice_generation(voice_service, text, emotion):
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


def voice_page():
    st.title("🎙️ Voice Studio")

    # Initialize voice service with error handling
    try:
        voice_service = VoiceService()
    except Exception as e:
        st.error(f"Failed to initialize voice service: {str(e)}")
        st.warning("""
            Voice features are currently unavailable. 
            Please ensure:
            1. tts_Zono.py is in the correct location
            2. The zonos package is properly installed
        """)
        return

    # Section 1: Voice Preview Generator
    with st.expander("🎚️ Voice Preview Lab", expanded=True):
        preview_col1, preview_col2 = st.columns([3, 1])

        with preview_col1:
            preview_text = st.text_area(
                "Enter text to vocalize",
                value="Hello there! How can I help you today?",
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
                    handle_voice_generation(voice_service, preview_text, emotion)

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

    # Section 2: Assign Voice to Bot (if applicable)
    if 'user_bots' in st.session_state and st.session_state.user_bots:
        with st.expander("🤖 Assign Voice to Bot"):
            selected_bot = st.selectbox(
                "Select Bot",
                options=[bot["name"] for bot in st.session_state.user_bots],
                key="voice_bot_selection"
            )

            assigned_emotion = st.selectbox(
                "Voice Profile",
                options=voice_service.get_available_emotions(),
                key="voice_assignment_emotion"
            )

            if st.button("Assign Voice", key="assign_voice"):
                st.warning("Voice assignment to bots is not implemented yet")

    # Section 3: Voice Management
    with st.expander("⚙️ Voice Profiles"):
        st.write("Available voice profiles:")
        for emotion in voice_service.get_available_emotions():
            st.write(f"- {emotion.capitalize()}")

        st.write("\nTo add new voice profiles, place reference audio files in:")

        # Get the config safely
        try:
            config = voice_service.config
            audio_ref_dir = config.get("audio_ref_dir", "Unknown directory")
            st.code(str(audio_ref_dir))
        except Exception as e:
            st.error(f"Could not retrieve configuration: {str(e)}")
            st.code("Please check the voice service configuration")