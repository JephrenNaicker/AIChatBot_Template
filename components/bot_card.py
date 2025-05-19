import streamlit as st


def bot_card(bot, show_actions=True, key_suffix="", on_chat=None):
    """
    Enhanced bot card component with all styling

    Args:
        bot (dict): Bot dictionary with name, emoji, desc, tags
        show_actions (bool): Whether to show action buttons
        key_suffix (str): Unique suffix for streamlit keys
        on_chat (function): Callback when chat button is clicked
    """
    unique_key = f"{bot['name']}_{key_suffix}"

    with st.container():
        # Card container with custom styling
        with st.container(border=True):
            # Header with emoji and name
            cols = st.columns([1, 4])
            with cols[0]:
                st.markdown(f"<div style='font-size: 2rem; text-align: center;'>{bot['emoji']}</div>",
                            unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"<h3 style='margin-bottom: 0.2rem;'>{bot['name']}</h3>",
                            unsafe_allow_html=True)
                st.markdown(f"<p style='color: #666; margin-bottom: 0.5rem;'>{bot['desc']}</p>",
                            unsafe_allow_html=True)

            # Tags display
            if bot.get('tags'):
                tags_html = '<div style="display: flex; flex-wrap: wrap; gap: 0.3rem; margin: 0.5rem 0;">'
                tags_html += ''.join(
                    [f'<span style="background: #2a3b4d; color: #7fbbde; padding: 0.2rem 0.6rem; '
                     f'border-radius: 1rem; font-size: 0.75rem;">{tag}</span>'
                     for tag in bot['tags']]
                )
                tags_html += '</div>'
                st.markdown(tags_html, unsafe_allow_html=True)

            # Action buttons
            if show_actions:
                if st.button(
                        "Chat",
                        key=f"chat_{unique_key}",
                        use_container_width=True,
                        on_click=on_chat if on_chat else (lambda: None)
                ):
                    if not on_chat:
                        st.session_state.selected_bot = bot['name']
                        st.session_state.page = "chat"
                        st.rerun()