# components/bot_card_home.py
import streamlit as st
from components.bot_card import get_bot_card_css, _get_portrait_avatar_html


def home_bot_card(bot, key_suffix=""):
    """
    Bot card for home page with expanding hover showing tags and details
    """
    unique_key = f"home_{bot['name']}_{key_suffix}"

    # Get avatar HTML for background
    avatar_html = _get_portrait_avatar_html(bot)

    # Create tags HTML if tags exist
    tags_html = ""
    if bot.get('tags'):
        tags_html = '<div class="bot-tags">'
        tags_html += ''.join(
            f'<span class="bot-tag">{tag}</span>' for tag in bot['tags']
        )
        tags_html += '</div>'

    # Get emoji
    emoji = bot.get('emoji', '🤖')

    # Create the HTML content with expanding hover info
    html_content = f"""
    <div class="portrait-card">
        {avatar_html}
        <div class="portrait-card-content">
            <div class="portrait-card-name">{bot['name']}</div>
            <div class="portrait-card-desc">{bot['desc'][:100]}{'...' if len(bot['desc']) > 100 else ''}</div>
        </div>

        <div class="bot-info-expanded">
            <div class="bot-emoji">{emoji}</div>
            <h4>{bot['name']}</h4>

            {f'<div class="bot-tags-container"><div class="bot-tags-title">TAGS</div>{tags_html}</div>' if bot.get('tags') else ''}

            <div class="bot-description">{bot['desc']}</div>

            <div class="bot-action-hint">
                💬 Click "Chat" to start conversation
            </div>
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