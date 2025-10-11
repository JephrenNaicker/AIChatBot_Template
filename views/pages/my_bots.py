# views/pages/my_bots.py
import streamlit as st
from controllers.bot_manager_controller import BotManager
from components.bot_card import bot_card, get_bot_card_css


async def my_bots_page():
    """Main entry point for the My Bots page"""
    # Handle pending bot actions first
    if 'pending_bot_action' in st.session_state:
        action = st.session_state.pending_bot_action
        if action["type"] == "delete":
            await BotManager._delete_bot(action["bot_name"])
        elif action["type"] == "update_status":
            await BotManager._update_bot_status(action["bot_name"], action["new_status"])
        # Clear the pending action
        del st.session_state.pending_bot_action

    # Inject CSS
    st.markdown(get_bot_card_css(), unsafe_allow_html=True)

    st.title("🌟 My Custom Bots")
    BotManager.fix_coroutine_avatars()

    if not st.session_state.user_bots:
        BotManager.show_empty_state()
        return

    # Status filter
    filtered_bots = BotManager.filter_bots_by_status()

    if not filtered_bots:
        st.info(f"No bots match the filter: {st.session_state.get('bot_status_filter', 'All')}")
        return

    # Display bots using management cards
    cols = st.columns(2)
    for i, bot in enumerate(filtered_bots):
        with cols[i % 2]:
            bot_card(bot=bot, mode="manage", key_suffix=str(i))

    if st.button("➕ Create Another Bot"):
        st.session_state.page = "bot_setup"
        st.rerun()