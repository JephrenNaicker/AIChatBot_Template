import streamlit as st
from config import PAGES
from components.avatar_utils import get_avatar_display
from config import DEFAULT_BOTS
from models.bot import Bot


def get_sidebar_css():
    return """
    <style>
    /* Sidebar container */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
        padding: 1.5rem 1rem;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Sidebar header */
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #e2e8f0 !important;
        text-align: center;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }

    /* Navigation buttons */
    div[data-testid="stVerticalBlock"] button[kind="secondary"] {
        background-color: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        transition: all 0.2s ease-in-out !important;
        font-weight: 500 !important;
    }

    /* Hover and active effects */
    div[data-testid="stVerticalBlock"] button[kind="secondary"]:hover {
        background-color: #334155 !important;
        transform: translateY(-1px);
        box-shadow: 0 0 6px rgba(59, 130, 246, 0.4);
    }

    /* Chat section */
    section[data-testid="stSidebar"] .stSubheader {
        color: #94a3b8 !important;
        text-transform: uppercase;
        font-size: 0.8rem !important;
        margin-top: 1.5rem !important;
        letter-spacing: 0.06em;
    }

    /* Chat buttons styling */
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        transition: all 0.2s ease-in-out !important;
        font-weight: 400 !important;
        text-align: left !important;
        padding: 0.5rem 0.75rem !important;
        margin-bottom: 0.5rem !important;
    }

    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #334155 !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
    }

    /* Active chat button */
    section[data-testid="stSidebar"] button[kind="secondary"].active-chat {
        background-color: rgba(59, 130, 246, 0.15) !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
        color: #60a5fa !important;
    }

    /* Delete buttons */
    section[data-testid="stSidebar"] button[kind="secondary"].delete-btn {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        color: #94a3b8 !important;
        opacity: 0.7;
        padding: 0.25rem 0.5rem !important;
        min-width: auto !important;
    }

    section[data-testid="stSidebar"] button[kind="secondary"].delete-btn:hover {
        background-color: rgba(239, 68, 68, 0.1) !important;
        border-color: rgba(239, 68, 68, 0.3) !important;
        color: #ef4444 !important;
        opacity: 1;
    }

    /* Avatar alignment */
    section[data-testid="stSidebar"] [data-testid="column"] {
        align-items: center;
    }

    /* Empty chats message */
    .empty-chats {
        text-align: center;
        color: #94a3b8;
        font-size: 0.9rem;
        padding: 1.5rem 0.5rem;
        line-height: 1.5;
    }

    /* Divider */
    section[data-testid="stSidebar"] hr {
        margin: 1.5rem 0;
        border-color: rgba(255, 255, 255, 0.1);
    }

    /* Scrollbar styling */
    section[data-testid="stSidebar"] ::-webkit-scrollbar {
        width: 6px;
    }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.3);
        border-radius: 3px;
    }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
        background: rgba(148, 163, 184, 0.5);
    }
    </style>
    """


async def create_sidebar():
    """Reusable sidebar component with navigation and chat history"""
    with st.sidebar:
        st.markdown(get_sidebar_css(), unsafe_allow_html=True)

        st.header("📚 StoryBot")

        # Navigation buttons
        nav_cols = st.columns(2)
        with nav_cols[0]:
            if st.button(PAGES["home"], use_container_width=True, key="nav_home"):
                st.session_state.page = "home"
                st.rerun()
        with nav_cols[1]:
            if st.button(PAGES["profile"], use_container_width=True, key="nav_profile"):
                st.session_state.page = "profile"
                st.rerun()

        # Additional navigation items
        if st.button(PAGES["my_bots"], use_container_width=True, key="nav_my_bots"):
            st.session_state.page = "my_bots"
            st.rerun()

        if st.button(PAGES["voice"], use_container_width=True, key="nav_voice"):
            st.session_state.page = "voice"
            st.rerun()

        if st.button(PAGES["image_studio"], use_container_width=True, key="nav_image_studio"):
            st.session_state.page = "image_studio"
            st.rerun()

        if st.button(PAGES["group_chat"], use_container_width=True, key="nav_group_chat"):
            st.session_state.page = "group_chat"
            st.rerun()

        st.divider()
        await _display_chat_list()


# Update the _display_chat_list function:
async def _display_chat_list():
    """Private method to display chat history list"""
    st.subheader("💬 Your Chats")

    if 'chat_histories' not in st.session_state:
        st.session_state.chat_histories = {}

    if not st.session_state.chat_histories:
        st.markdown('<div class="empty-chats">No chats yet<br>Start a conversation!</div>', unsafe_allow_html=True)
        return

    # Get all bots - user bots (dicts) + default bots (Bot objects)
    user_bots = st.session_state.get('user_bots', [])
    all_bots = DEFAULT_BOTS + user_bots  # This mixes Bot objects and dicts

    for bot_name in list(st.session_state.chat_histories.keys()):
        # Find the bot by name - handle both Bot objects and dictionaries
        bot = None
        for b in all_bots:
            # Check if it's a Bot object or dictionary
            if hasattr(b, 'name'):  # Bot object
                if b.name == bot_name:
                    bot = b
                    break
            elif isinstance(b, dict) and b.get('name') == bot_name:  # Dictionary
                bot = b
                break

        if not bot:
            continue

        # Get avatar for display - handle both Bot objects and dictionaries
        if hasattr(bot, 'get_avatar_display'):  # Bot object
            avatar = bot.get_avatar_display()
            display_name = bot.name
        else:  # Dictionary
            # For dictionaries, use the emoji field or default to 🤖
            avatar = bot.get('emoji', '🤖')
            display_name = bot.get('name', 'Unknown Bot')

        is_active = st.session_state.get('selected_bot') == bot_name and st.session_state.get('page') == 'chat'

        # Create a single row with proper spacing
        col1, col2, col3 = st.columns([1, 4, 1])

        with col1:
            # Display avatar - handle both emoji and image
            if isinstance(avatar, str) and len(avatar) <= 3:  # Emoji
                st.write(avatar)
            else:  # Image or complex string
                st.image(avatar, width=32)

        with col2:
            # Chat selection button - full width
            button_label = f"**{display_name}**" if is_active else display_name
            if st.button(button_label, key=f"select_{bot_name}", use_container_width=True):
                st.session_state.selected_bot = bot_name
                st.session_state.page = "chat"
                st.rerun()

        with col3:
            # Delete button with icon
            if st.button("🗑️", key=f"delete_{bot_name}", help=f"Delete chat with {display_name}"):
                if st.session_state.get('selected_bot') == bot_name:
                    st.session_state.selected_bot = None
                    st.session_state.page = "home"
                del st.session_state.chat_histories[bot_name]
                st.rerun()

        # Add some spacing between chat entries
        st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)