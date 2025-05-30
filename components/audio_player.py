import streamlit as st
import os
from pathlib import Path
from datetime import datetime

def audio_player(audio_path: str, autoplay: bool = False, downloadable: bool = True, key: str = None):
    """
    Enhanced audio player component with more features

    Args:
        audio_path (str): Path to audio file
        autoplay (bool): Whether to autoplay the audio
        downloadable (bool): Show download button
        key (str): Unique key for Streamlit components
    """
    try:
        # Validate input path
        if not audio_path or not isinstance(audio_path, (str, Path)):
            st.warning("Invalid audio path")
            return

        # Convert to Path object and verify existence
        audio_file = Path(audio_path)
        if not audio_file.exists():
            st.warning(f"Audio file not found at: {str(audio_file)}")
            return

        with st.container(border=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                # Main audio player with explicit string conversion
                st.audio(str(audio_file), format="audio/wav", autoplay=autoplay)

                # Safely generate file info
                try:
                    file_size = audio_file.stat().st_size / 1024  # KB
                    mod_time = datetime.fromtimestamp(audio_file.stat().st_mtime)
                    file_info = f"""
                        File: {audio_file.name}  
                        Size: {file_size:.1f} KB  
                        Modified: {mod_time.strftime('%Y-%m-%d %H:%M')}
                    """
                except Exception as e:
                    file_info = f"File: {audio_file.name}"
                    st.warning(f"Couldn't read file metadata: {e}")

                st.caption(file_info)

            with col2:
                # Download button
                if downloadable:
                    try:
                        with open(audio_file, "rb") as f:
                            st.download_button(
                                label="⬇️",
                                data=f,
                                file_name=audio_file.name,
                                mime="audio/wav",
                                key=f"download_{key}" if key else None
                            )
                    except Exception as e:
                        st.error(f"Download failed: {e}")

                # Delete button
                if st.button("🗑️", key=f"delete_{key}" if key else None):
                    try:
                        audio_file.unlink()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Couldn't delete file: {e}")

    except Exception as e:
        st.error(f"Audio player error: {e}")
        # Fallback to basic player if everything else fails
        st.audio(str(audio_path))