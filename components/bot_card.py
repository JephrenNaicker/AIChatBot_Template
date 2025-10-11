# components/bot_card.py
import streamlit as st
import os
import asyncio
import base64


def bot_card(bot, mode="home", show_actions=True, key_suffix="", on_chat=None, on_edit=None, on_delete=None,
             on_publish=None):
    """
    Unified bot card component for all pages

    Parameters:
    - bot: Bot dictionary
    - mode: "home" (gallery) or "manage" (my bots)
    - show_actions: Whether to show action buttons
    - key_suffix: Unique key suffix for Streamlit elements
    - on_chat, on_edit, on_delete, on_publish: Custom callback functions
    """
    unique_key = f"{mode}_{bot['name']}_{key_suffix}"

    if mode == "home":
        return _home_bot_card(bot, show_actions, unique_key, on_chat)
    elif mode == "manage":
        return _manage_bot_card(bot, show_actions, unique_key, on_chat, on_edit, on_delete, on_publish)
    else:
        return _default_bot_card(bot, show_actions, unique_key, on_chat)


def _home_bot_card(bot, show_actions, unique_key, on_chat):
    """Bot card for home page with expanding hover showing tags and details"""
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
    if show_actions and st.button("💬 Chat", key=f"chat_{unique_key}", use_container_width=True):
        _handle_chat_click(bot, on_chat)


def _manage_bot_card(bot, show_actions, unique_key, on_chat, on_edit, on_delete, on_publish):
    """Bot card for my bots page - full management with edit/delete/publish options"""
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
    if show_actions:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("💬 Chat", key=f"chat_{unique_key}", use_container_width=True):
                _handle_chat_click(bot, on_chat)

        with col2:
            if st.button("✏️ Edit", key=f"edit_{unique_key}", use_container_width=True):
                if on_edit:
                    on_edit(bot)
                else:
                    st.session_state.editing_bot = bot
                    st.session_state.page = "edit_bot"
                    st.rerun()

        # Second row of buttons
        col3, col4 = st.columns(2)

        with col3:
            if status == "draft":
                if st.button("🚀 Publish", key=f"publish_{unique_key}", use_container_width=True):
                    if on_publish:
                        on_publish(bot)
                    else:
                        from controllers.bot_manager_controller import BotManager
                        BotManager._update_bot_status(bot["name"], "published")
            else:
                if st.button("📦 Unpublish", key=f"unpublish_{unique_key}", use_container_width=True):
                    if on_publish:  # Reuse on_publish for unpublish too
                        on_publish(bot, "draft")
                    else:
                        from controllers.bot_manager_controller import BotManager
                        BotManager._update_bot_status(bot["name"], "draft")

        with col4:
            if st.button("🗑️ Delete", key=f"delete_{unique_key}", use_container_width=True):
                if on_delete:
                    on_delete(bot)
                else:
                    from controllers.bot_manager_controller import BotManager
                    BotManager._delete_bot(bot["name"])


def _default_bot_card(bot, show_actions, unique_key, on_chat):
    """Default bot card layout (backward compatibility)"""
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
        on_chat(bot)
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
            # Fallback to enhanced emoji background
            return _get_enhanced_emoji_background(bot)

    # Handle emoji background with enhanced styling
    else:
        return _get_enhanced_emoji_background(bot)


def _get_enhanced_emoji_background(bot):
    """Create a more visually appealing emoji background"""
    emoji = bot.get("emoji", "🤖")

    # Different gradient backgrounds based on bot type or random
    gradients = [
        "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
        "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)"
    ]

    # Choose gradient based on emoji hash for consistency
    gradient_index = hash(emoji) % len(gradients)
    selected_gradient = gradients[gradient_index]

    return f'''
    <div style="width: 100%; height: 100%; background: {selected_gradient}; 
              display: flex; align-items: center; justify-content: center; border-radius: 16px;
              box-shadow: inset 0 0 20px rgba(0,0,0,0.1);">
        <span style="font-size: 4rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{emoji}</span>
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
    """Return comprehensive CSS for all bot card variants"""
    return """
    <style>
        /* Base portrait card styles */
        .portrait-card {
            width: 200px;
            height: 280px;
            border-radius: 16px;
            position: relative;
            overflow: hidden;
            margin: 0 auto 1rem auto;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            background: white;
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
            color: white !important;
        }

        .portrait-card-desc {
            font-size: 0.85rem;
            opacity: 0.9;
            height: 40px;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            color: white !important;
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

        /* Home page specific styles with hover effects */
        .portrait-card {
            transition: all 0.4s ease;
            cursor: pointer;
        }

        .portrait-card:hover {
            height: 380px;
            transform: translateY(-10px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.3) !important;
            z-index: 10;
        }

        .portrait-card:hover .portrait-card-content {
            opacity: 0;
        }

        .bot-info-expanded {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(20,20,40,0.98) 0%, rgba(40,40,60,0.98) 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 16px;
            opacity: 0;
            transition: opacity 0.3s ease;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            text-align: center;
            overflow-y: auto;
            transform: translateY(20px);
        }

        .portrait-card:hover .bot-info-expanded {
            opacity: 1;
            transform: translateY(0);
        }

        .bot-info-expanded h4 {
            margin: 0 0 1rem 0;
            font-size: 1.3rem;
            font-weight: bold;
            color: #fff;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }

        .bot-info-expanded .bot-description {
            margin: 0 0 1rem 0;
            font-size: 0.9rem;
            line-height: 1.4;
            opacity: 0.9;
        }

        .bot-tags-container {
            margin: 0.5rem 0 1rem 0;
            width: 100%;
        }

        .bot-tags-title {
            font-size: 0.8rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            opacity: 0.8;
            color: #a0a0ff;
        }

        .bot-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            justify-content: center;
        }

        .bot-tag {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        .bot-emoji {
            font-size: 2.5rem;
            margin-bottom: 0.8rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        .bot-action-hint {
            margin-top: auto;
            padding: 0.8rem;
            background: rgba(255,255,255,0.15);
            border-radius: 10px;
            font-size: 0.8rem;
            opacity: 0.9;
            border: 1px solid rgba(255,255,255,0.2);
            width: 100%;
            box-sizing: border-box;
        }

        /* Scrollbar styling */
        .bot-info-expanded::-webkit-scrollbar {
            width: 4px;
        }

        .bot-info-expanded::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.1);
            border-radius: 2px;
        }

        .bot-info-expanded::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.3);
            border-radius: 2px;
        }

        .bot-info-expanded::-webkit-scrollbar-thumb:hover {
            background: rgba(255,255,255,0.5);
        }

        /* Grid layout helpers */
        .full-width-grid {
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
        }

        .bot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }

        /* Ensure cards don't overlap when expanded */
        .stColumn {
            position: relative;
            z-index: 1;
        }

        .stColumn:hover {
            z-index: 10;
        }
    </style>
    """