import streamlit as st
from config import BOTS, PAGES
from components.bot_card import bot_card

def home_page():
    """Home page with title/search in centered container and full-width grid"""
    st.title("🤖 Chat Bot Gallery")
    search_query = st.text_input("🔍 Search bots...",
                                placeholder="Type to filter bots",
                                key="bot_search")

    # Separate default bots and user bots
    default_bots = BOTS
    user_bots = [
        bot for bot in st.session_state.user_bots
        if bot.get("status", "draft") == "published" or
           bot.get("creator", "") == st.session_state.profile_data.get("username", "")
    ]

    # Filter bots
    filtered_default_bots = [
        bot for bot in default_bots
        if not search_query or
           (search_query.lower() in bot["name"].lower() or
            search_query.lower() in bot["desc"].lower() or
            any(search_query.lower() in tag.lower() for tag in bot["tags"]))
    ]

    filtered_user_bots = [
        bot for bot in user_bots
        if not search_query or
           (search_query.lower() in bot["name"].lower() or
            search_query.lower() in bot["desc"].lower() or
            any(search_query.lower() in tag.lower() for tag in bot.get("tags", [])))
    ]

    # Create full-width container for the grid
    st.markdown('<div class="full-width-grid">', unsafe_allow_html=True)

    # Display default bots section
    if filtered_default_bots:
        cols = st.columns(3)
        for i, bot in enumerate(filtered_default_bots):
            with cols[i % 3]:
                bot_card(
                    bot=bot,
                    show_actions=True,
                    key_suffix=f"default_{i}",
                    on_chat=lambda b=bot: set_bot_and_redirect(b)
                )

    # Divider and user bots section
    if filtered_user_bots:
        st.divider()
        cols = st.columns(3)
        for i, bot in enumerate(filtered_user_bots):
            with cols[i % 3]:
                bot_card(
                    bot=bot,
                    show_actions=True,
                    key_suffix=f"custom_{i}",
                    on_chat=lambda b=bot: set_bot_and_redirect(b)
                )

    # Close our full-width div
    st.markdown('</div>', unsafe_allow_html=True)

    # Empty state
    if search_query and not filtered_default_bots and not filtered_user_bots:
        st.warning("No bots match your search. Try different keywords.")
        if st.button("Clear search", key="clear_search"):
            st.rerun()

def set_bot_and_redirect(bot):
    """Helper function to set bot and redirect to chat"""
    st.session_state.selected_bot = bot['name']
    st.session_state.page = "chat"
    st.rerun()