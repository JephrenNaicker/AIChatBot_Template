import streamlit as st

async def bot_setup_page():
    st.title("🧙 Character Creation")
    st.write("Choose your creation method:")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🪄 AI-Assisted Creation",
                     help="Generate a character concept with AI",
                     use_container_width=True):
            st.session_state.page = "generate_concept"
            st.rerun()

    with col2:
        if st.button("✏️ Manual Creation",
                     help="Build from scratch",
                     use_container_width=True):
            st.session_state.page = "create_bot"
            st.rerun()
