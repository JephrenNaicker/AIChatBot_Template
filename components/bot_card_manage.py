# components/bot_card_manage.py
import streamlit as st
import os
import base64
from components.bot_card import get_bot_card_css, _get_portrait_avatar_html


def manage_bot_card(bot, key_suffix=""):
    """
    Bot card for my bots page - full management with edit/delete/publish options
    """
    unique_key = f"manage_{bot['name']}_{key_suffix}"

    # Get avatar HTML for background
    avatar_html = _get_portrait_avatar_html(bot)

    # Status badge
    status = bot.get("status", "draft")
    status_color = "#f39c12" if status == "draft" else "#2ecc71"
    status_text = "DRAFT" if status == "draft" else "PUBLISHED"

    # Create the HTML content
    html_content = f"""
    <div class="portrait-card">
        {avatar_html}
        <span class="status-badge status-{status}" style="background: {status_color};">{status_text}</span>
        <div class="portrait-card-content">
            <div class="portrait-card-name">{bot['name']}</div>
            <div class="portrait-card-desc">{bot['desc'][:100]}{'...' if len(bot['desc']) > 100 else ''}</div>
        </div>
    </div>
    """

    # Display the card
    st.markdown(html_content, unsafe_allow_html=True)

    # Action buttons in two rows
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💬 Chat", key=f"chat_{unique_key}", use_container_width=True):
            st.session_state.selected_bot = bot['name']
            st.session_state.page = "chat"
            st.rerun()

    with col2:
        if st.button("✏️ Edit", key=f"edit_{unique_key}", use_container_width=True):
            st.session_state.editing_bot = bot
            st.session_state.page = "edit_bot"
            st.rerun()

    # Second row of buttons
    col3, col4 = st.columns(2)

    with col3:
        if status == "draft":
            if st.button("🚀 Publish", key=f"publish_{unique_key}", use_container_width=True):
                # Call publish method
                from controllers.bot_manager_controller import BotManager
                BotManager._update_bot_status(bot["name"], "published")
        else:
            if st.button("📦 Unpublish", key=f"unpublish_{unique_key}", use_container_width=True):
                # Call unpublish method
                from controllers.bot_manager_controller import BotManager
                BotManager._update_bot_status(bot["name"], "draft")

    with col4:
        if st.button("🗑️ Delete", key=f"delete_{unique_key}", use_container_width=True):
            # Call delete method
            from controllers.bot_manager_controller import BotManager
            BotManager._delete_bot(bot["name"])