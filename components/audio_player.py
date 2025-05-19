import streamlit as st
import os
from pathlib import Path


def audio_player(audio_path: str, autoplay: bool = False, downloadable: bool = True, key: str = None):
    """
    Enhanced audio player component with more features

    Args:
        audio_path (str): Path to audio file
        autoplay (bool): Whether to autoplay the audio
        downloadable (bool): Show download button
        key (str): Unique key for Streamlit components
    """
    if not audio_path or not os.path.exists(audio_path):
        st.warning("Audio file not found")
        return

    with st.container(border=True):
        col1, col2 = st.columns([4, 1])

        with col1:
            # Main audio player
            st.audio(audio_path, format="audio/wav", autoplay=autoplay)

            # Audio info
            audio_file = Path(audio_path)
            st.caption(f"""
                File: {audio_file.name}  
                Size: {audio_file.stat().st_size / 1024:.1f} KB  
                Modified: {audio_file.stat().st_mtime:%Y-%m-%d %H:%M}
            """)

        with col2:
            # Download button
            if downloadable:
                with open(audio_path, "rb") as f:
                    st.download_button(
                        label="⬇️",
                        data=f,
                        file_name=audio_file.name,
                        mime="audio/wav",
                        key=f"download_{key}" if key else None
                    )

            # Delete button
            if st.button("🗑️", key=f"delete_{key}" if key else None):
                try:
                    os.remove(audio_path)
                    st.rerun()
                except Exception as e:
                    st.error(f"Couldn't delete file: {e}")