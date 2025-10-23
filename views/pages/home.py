# views/pages/home.py
import streamlit as st
from config import DEFAULT_BOTS
from components.bot_card import bot_card, get_bot_card_css


# Update the home_page function:
async def home_page():
    """Home page with view/chat only bot cards with enhanced hover"""
    # Inject CSS for bot cards with enhanced hover effects
    st.markdown(get_bot_card_css(), unsafe_allow_html=True)

    st.title("🤖 Chat Bot Gallery")
    search_query = st.text_input("🔍 Search bots...",
                                 placeholder="Type to filter bots",
                                 key="bot_search")

    # Prepare default bots - using Bot objects
    default_bots = DEFAULT_BOTS

    # Prepare user bots (only published ones for home page) - these are DICTIONARIES
    user_bots = [
        bot for bot in st.session_state.get('user_bots', [])
        if bot.get('status') == "published"  # Use .get() for dictionaries
    ]

    # Filter default bots - handle Bot objects
    filtered_default_bots = [
        bot for bot in default_bots
        if not search_query or
           (search_query.lower() in bot.name.lower() or
            search_query.lower() in bot.desc.lower() or
            any(search_query.lower() in tag.lower() for tag in bot.tags))
    ]

    # Filter user bots - handle DICTIONARIES
    filtered_user_bots = [
        bot for bot in user_bots
        if not search_query or
           (search_query.lower() in bot.get('name', '').lower() or
            search_query.lower() in bot.get('desc', '').lower() or
            any(search_query.lower() in tag.lower() for tag in bot.get('tags', [])))
    ]

    # Display default bots section
    if filtered_default_bots:
        st.subheader("🌟 Default Bots")
        cols = st.columns(3)
        for i, bot in enumerate(filtered_default_bots):
            with cols[i % 3]:
                # Convert Bot object to dict for bot_card compatibility
                bot_dict = bot.to_dict()
                bot_card(bot=bot_dict, mode="home", key_suffix=f"default_{i}")

    # Divider and user bots section
    if filtered_user_bots:
        st.divider()
        st.subheader("🎨 Community Bots")
        cols = st.columns(3)
        for i, bot in enumerate(filtered_user_bots):
            with cols[i % 3]:
                # User bots are already dictionaries, no conversion needed
                bot_card(bot=bot, mode="home", key_suffix=f"custom_{i}")

    # Empty states
    if search_query and not filtered_default_bots and not filtered_user_bots:
        st.warning("No bots match your search. Try different keywords.")
        if st.button("Clear search", key="clear_search"):
            st.rerun()

    if not search_query and not filtered_default_bots and not filtered_user_bots:
        st.info("No bots available yet. Be the first to create one!")
        if st.button("Create Your First Bot", key="create_first_bot"):
            st.session_state.page = "bot_setup"
            st.rerun()


def set_bot_and_redirect(bot):
    """Helper function to set bot and redirect to chat"""
    # Handle both Bot objects and dictionaries
    if hasattr(bot, 'name'):  # Bot object
        bot_name = bot.name
    else:  # Dictionary
        bot_name = bot.get('name')

    st.session_state.selected_bot = bot_name
    st.session_state.page = "chat"
    st.rerun()