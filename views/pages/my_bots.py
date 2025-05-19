import streamlit as st
from controllers.bot_manager_controller import BotManager

def my_bots_page():
    """Main entry point for the My Bots page"""
    st.title("🌟 My Custom Bots")

    if not st.session_state.user_bots:
        BotManager._show_empty_state()
        return

    filtered_bots = BotManager._filter_bots_by_status()

    if not filtered_bots:
        st.info(f"No bots match the filter: {st.session_state.get('bot_status_filter', 'All')}")
        return

    BotManager._display_bots_grid(filtered_bots)

    if st.button("➕ Create Another Bot"):
        st.session_state.page = "bot_setup"
        st.rerun()