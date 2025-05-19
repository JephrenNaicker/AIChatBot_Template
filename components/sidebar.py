import streamlit as st
from config import PAGES


def create_sidebar():
    """Reusable sidebar component with navigation and chat history"""
    with st.sidebar:
        st.header("📚 StoryBot")

        # Navigation buttons
        nav_cols = st.columns(2)
        with nav_cols[0]:
            if st.button(PAGES["home"], use_container_width=True, key="nav_home"):
                st.session_state.page = "home"
                st.rerun()
        with nav_cols[1]:
            if st.button(PAGES["profile"], use_container_width=True, key="nav_profile"):
                st.session_state.page = "profile"
                st.rerun()

        # Additional navigation items
        if st.button(PAGES["my_bots"], use_container_width=True, key="nav_my_bots"):
            st.session_state.page = "my_bots"
            st.rerun()

        if st.button(PAGES["voice"], use_container_width=True, key="nav_voice"):
            st.session_state.page = "voice"
            st.rerun()

        if st.button(PAGES["group_chat"], use_container_width=True, key="nav_group_chat"):
            st.session_state.page = "group_chat"
            st.rerun()

        st.divider()
        _display_chat_list()


def _display_chat_list():
    """Private method to display chat history list"""
    st.subheader("Your Chats")

    if 'chat_histories' not in st.session_state:
        st.session_state.chat_histories = {}

    for bot_name in list(st.session_state.chat_histories.keys()):
        cols = st.columns([1, 4, 1])
        with cols[0]:
            # Get emoji from either default bots or user bots
            all_bots = st.session_state.get('bots', []) + st.session_state.user_bots
            bot_emoji = next((b['emoji'] for b in all_bots if b['name'] == bot_name), "🤖")
            st.write(bot_emoji)

        with cols[1]:
            if st.button(bot_name, key=f"select_{bot_name}"):
                st.session_state.selected_bot = bot_name
                st.session_state.page = "chat"
                st.rerun()

        with cols[2]:
            if st.button("🗑️", key=f"delete_{bot_name}"):
                if st.session_state.get('selected_bot') == bot_name:
                    st.session_state.selected_bot = None
                    st.session_state.page = "home"
                del st.session_state.chat_histories[bot_name]
                st.rerun()