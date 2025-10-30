# views/pages/home.py
import streamlit as st
from config import get_default_bots
from components.bot_card import bot_card, get_bot_card_css
from typing import List, Union, Dict, Any


async def home_page():
    """Home page with view/chat only bot cards with enhanced hover"""
    # Inject CSS for bot cards with enhanced hover effects
    st.markdown(get_bot_card_css(), unsafe_allow_html=True)

    st.title("🤖 Chat Bot Gallery")
    search_query = st.text_input("🔍 Search bots...",
                                 placeholder="Type to filter bots",
                                 key="bot_search")

    # Prepare default bots - these are Bot objects
    default_bots = get_default_bots()

    # Prepare user bots (only published ones for home page)
    # Ensure we're working with Bot objects
    user_bots = []
    for bot in st.session_state.user_bots:
        # If it's a dictionary, convert to Bot object
        if isinstance(bot, dict):
            from models.bot import Bot
            bot_obj = Bot.from_dict(bot)
            user_bots.append(bot_obj)
        elif hasattr(bot, 'name'):
            if bot.is_published():
                user_bots.append(bot)

    # Filter bots using Bot object attributes
    filtered_default_bots = [
        bot for bot in default_bots
        if not search_query or
           (search_query.lower() in bot.name.lower() or
            search_query.lower() in bot.desc.lower() or
            any(search_query.lower() in tag.lower() for tag in bot.tags))
    ]

    filtered_user_bots = [
        bot for bot in user_bots
        if not search_query or
           (search_query.lower() in bot.name.lower() or
            search_query.lower() in bot.desc.lower() or
            any(search_query.lower() in tag.lower() for tag in bot.tags))
    ]

    # Display default bots section - PASS BOT OBJECTS DIRECTLY
    if filtered_default_bots:
        st.subheader("🌟 Default Bots")
        cols = st.columns(3)
        for i, bot in enumerate(filtered_default_bots):
            with cols[i % 3]:
                # PASS BOT OBJECT DIRECTLY - NO CONVERSION NEEDED
                bot_card(bot=bot, mode="home", key_suffix=f"default_{i}")

    # Divider and user bots section
    if filtered_user_bots:
        st.divider()
        st.subheader("🎨 Community Bots")
        cols = st.columns(3)
        for i, bot in enumerate(filtered_user_bots):
            with cols[i % 3]:
                # PASS BOT OBJECT DIRECTLY - NO CONVERSION NEEDED
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


def _bot_to_dict(bot) -> Dict[str, Any]:
    """Convert Bot object to dictionary for components that expect dict format"""
    if hasattr(bot, 'to_dict'):
        return bot.to_dict()
    elif isinstance(bot, dict):
        return bot
    else:
        # Fallback conversion
        return {
            "name": getattr(bot, 'name', 'Unknown'),
            "emoji": getattr(bot, 'emoji', '🤖'),
            "desc": getattr(bot, 'desc', ''),
            "tags": getattr(bot, 'tags', []),
            "status": getattr(bot, 'status', 'draft'),
            "personality": getattr(bot, 'personality', {}),
            "appearance": getattr(bot, 'appearance', {}),
            "voice": getattr(bot, 'voice', {}),
            "custom": getattr(bot, 'custom', True)
        }


def set_bot_and_redirect(bot):
    """Helper function to set bot and redirect to chat"""
    # Handle both Bot objects and dicts
    bot_name = bot.name if hasattr(bot, 'name') else bot['name']
    st.session_state.selected_bot = bot_name
    st.session_state.page = "chat"
    st.rerun()