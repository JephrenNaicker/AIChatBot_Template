# components/bot_card_home.py
import streamlit as st
from components.bot_card import _get_portrait_avatar_html


def home_bot_card(bot, key_suffix=""):
    """
    Bot card for home page - view/chat only, no edit/delete options
    """
    unique_key = f"home_{bot['name']}_{key_suffix}"

    # Use a container to ensure proper rendering
    with st.container():
        # Get avatar HTML for background
        avatar_html = _get_portrait_avatar_html(bot)

        # Create the HTML content
        html_content = f"""
        <div class="portrait-card">
            {avatar_html}
            <div class="portrait-card-content">
                <div class="portrait-card-name">{bot['name']}</div>
                <div class="portrait-card-desc">{bot['desc'][:100]}{'...' if len(bot['desc']) > 100 else ''}</div>
            </div>
        </div>
        """

        # Display the card
        st.markdown(html_content, unsafe_allow_html=True)

        # Single chat button
        if st.button("💬 Chat", key=f"chat_{unique_key}", use_container_width=True):
            st.session_state.selected_bot = bot['name']
            st.session_state.page = "chat"
            st.rerun()