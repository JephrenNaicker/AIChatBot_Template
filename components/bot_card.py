# components/bot_card.py
import streamlit as st
import os
import asyncio
import base64


def bot_card(bot, show_actions=True, key_suffix="", on_chat=None, variant="default"):
    """
    Enhanced bot card component with multiple variants including portrait style
    """
    unique_key = f"{bot['name']}_{key_suffix}"

    if variant == "portrait":
        return _portrait_bot_card(bot, show_actions, unique_key, on_chat)
    else:
        return _default_bot_card(bot, show_actions, unique_key, on_chat)


def _portrait_bot_card(bot, show_actions, unique_key, on_chat):
    """Portrait-style bot card with background image"""
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

    # Display the HTML
    st.markdown(html_content, unsafe_allow_html=True)

    # Action buttons
    if show_actions:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💬", key=f"chat_{unique_key}", help="Chat with bot", use_container_width=True):
                _handle_chat_click(bot, on_chat)
        with col2:
            if st.button("✏️", key=f"edit_{unique_key}", help="Edit bot", use_container_width=True):
                st.session_state.editing_bot = bot
                st.session_state.page = "edit_bot"
                st.rerun()
        with col3:
            if st.button("⚙️", key=f"options_{unique_key}", help="More options", use_container_width=True):
                st.session_state.selected_bot_for_options = bot
                st.rerun()


def _default_bot_card(bot, show_actions, unique_key, on_chat):
    """Default bot card layout"""
    with st.container():
        with st.container(border=True):
            cols = st.columns([1, 4])

            with cols[0]:
                avatar_html = _get_avatar_html(bot)
                st.markdown(avatar_html, unsafe_allow_html=True)

            with cols[1]:
                status_html = ""
                if bot.get("status") == "draft":
                    status_html = f'<span style="color: #f39c12; font-weight: bold; font-size: 0.8rem; margin-left: 8px;">DRAFT</span>'

                st.markdown(
                    f"<h3 style='margin-bottom: 0.2rem; display: flex; align-items: center;'>{bot['name']}{status_html}</h3>",
                    unsafe_allow_html=True)

                st.markdown(f"<p style='color: #666; margin-bottom: 0.5rem;'>{bot['desc']}</p>",
                            unsafe_allow_html=True)

            if bot.get('tags'):
                tags_html = '<div style="display: flex; flex-wrap: wrap; gap: 0.3rem; margin: 0.5rem 0;">'
                tags_html += ''.join(
                    [f'<span style="background: #2a3b4d; color: #7fbbde; padding: 0.2rem 0.6rem; '
                     f'border-radius: 1rem; font-size: 0.75rem;">{tag}</span>'
                     for tag in bot['tags']]
                )
                tags_html += '</div>'
                st.markdown(tags_html, unsafe_allow_html=True)

            if show_actions:
                if st.button(
                        "Chat",
                        key=f"chat_{unique_key}",
                        use_container_width=True,
                        on_click=lambda: _handle_chat_click(bot, on_chat)
                ):
                    pass


def _handle_chat_click(bot, on_chat):
    """Handle chat button click"""
    if on_chat:
        on_chat()
    else:
        st.session_state.selected_bot = bot['name']
        st.session_state.page = "chat"
        st.rerun()


def _get_portrait_avatar_html(bot):
    """Generate HTML for portrait-style avatar background"""
    avatar_data = bot.get("appearance", {}).get("avatar")

    # Handle image avatar
    if (avatar_data and
            isinstance(avatar_data, dict) and
            "filepath" in avatar_data and
            os.path.exists(avatar_data["filepath"])):

        try:
            with open(avatar_data["filepath"], "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()

            return f'<img src="data:image/jpeg;base64,{img_data}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 16px;">'
        except Exception as e:
            # Fallback to emoji background
            return f'''
            <div style="width: 100%; height: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      display: flex; align-items: center; justify-content: center; border-radius: 16px;">
                <span style="font-size: 3rem;">{bot.get("emoji", "🤖")}</span>
            </div>
            '''

    # Handle emoji background
    else:
        return f'''
        <div style="width: 100%; height: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  display: flex; align-items: center; justify-content: center; border-radius: 16px;">
            <span style="font-size: 3rem;">{bot.get("emoji", "🤖")}</span>
        </div>
        '''


def _get_avatar_html(bot):
    """Generate HTML for default avatar"""
    avatar_data = bot.get("appearance", {}).get("avatar")

    # Handle coroutine
    if asyncio.iscoroutine(avatar_data):
        return f'<div style="font-size: 2rem; text-align: center; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; background: #f0f2f6; border-radius: 8px;">{bot.get("emoji", "🤖")}</div>'

    # Handle image avatar
    elif (avatar_data and
          isinstance(avatar_data, dict) and
          "filepath" in avatar_data and
          os.path.exists(avatar_data["filepath"])):

        try:
            with open(avatar_data["filepath"], "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()

            return f'''
            <div style="width: 60px; height: 60px; display: flex; align-items: center; justify-content: center;">
                <img src="data:image/jpeg;base64,{img_data}" 
                     style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px; border: 2px solid #e0e0e0;">
            </div>
            '''
        except Exception as e:
            return f'<div style="font-size: 2rem; text-align: center; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; background: #f0f2f6; border-radius: 8px;">{bot.get("emoji", "🤖")}</div>'

    # Handle emoji avatar
    else:
        return f'<div style="font-size: 2rem; text-align: center; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; background: #f0f2f6; border-radius: 8px;">{bot.get("emoji", "🤖")}</div>'


def get_bot_card_css():
    """Return CSS for bot cards"""
    return """
    <style>
        .portrait-card {
            width: 200px;
            height: 280px;
            border-radius: 16px;
            position: relative;
            overflow: hidden;
            margin: 0 auto 1rem auto;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }

        .portrait-card-content {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 1rem;
            border-bottom-left-radius: 16px;
            border-bottom-right-radius: 16px;
        }

        .portrait-card-name {
            font-size: 1.1rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .portrait-card-desc {
            font-size: 0.85rem;
            opacity: 0.9;
            height: 40px;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }

        .status-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: bold;
        }

        .status-draft {
            background: #f39c12;
        }

        .status-published {
            background: #2ecc71;
        }
    </style>
    """