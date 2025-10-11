import streamlit as st
from langchain_community.chat_message_histories import ChatMessageHistory

# Import controllers
from controllers.voice_controller import VoiceService

# Import services
from components.sidebar import create_sidebar

# Import views (pages)
from views.pages.home import home_page
from views.pages.profile import profile_page
from views.pages.chat import chat_page
from views.pages.bot_setup import bot_setup_page
from views.pages.generate_concept import generate_concept_page
from views.pages.create_bot import create_bot_page
from views.pages.my_bots import my_bots_page
from views.pages.edit_bot import edit_bot_page
from views.pages.voice import voice_page
from views.pages.group_chat import group_chat_page
from services.image_service import ImageService
from views.pages.image_studio import image_studio_page


# Import bot card CSS
from components.bot_card import get_bot_card_css

# Initialize the service (add to your service initialization section)
image_service = ImageService(upload_dir="avatars", max_size_mb=5)
st.session_state.image_service = image_service


def initialize_chat_memory():
    """Initialize and return a properly configured conversation memory"""
    return {
        'chat_history': ChatMessageHistory(),
        'window_size': 20  # Keep last 20 messages
    }


def initialize_session_state():
    """Initialize all required session state variables"""
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    if 'selected_bot' not in st.session_state:
        st.session_state.selected_bot = None
    if 'greeting_sent' not in st.session_state:
        st.session_state.greeting_sent = False
    if 'memory' not in st.session_state:
        st.session_state.memory = initialize_chat_memory()
    if 'image_service' not in st.session_state:
        st.session_state.image_service = ImageService(upload_dir="avatars", max_size_mb=5)
    if 'voice_service' not in st.session_state:
        try:
            st.session_state.voice_service = VoiceService()
            st.session_state.voice_available = True
            print("VoiceService initialized successfully!")
            print("Available emotions:", st.session_state.voice_service.get_available_emotions())
        except Exception as e:
            print(f"VoiceService initialization failed: {e}")
            st.session_state.voice_service = None
            st.session_state.voice_available = False

    if 'group_chat' not in st.session_state:
        st.session_state.group_chat = {
            'active': False,
            'bots': [],
            'histories': {},
            'personality_memories': {},
            'shared_memory': initialize_chat_memory(),  # Using the new function
            'responder_idx': 0,
            'auto_mode': False,
            'last_interaction': None  # Added for tracking
        }
    if 'user_bots' not in st.session_state:
        st.session_state.user_bots = []
    if 'chat_histories' not in st.session_state:
        st.session_state.chat_histories = {}
    if 'profile_data' not in st.session_state:
        st.session_state.profile_data = {
            "username": "user_123",
            "display_name": "StoryLover",
            "bio": "I love chatting with AI characters!",
            "avatar": "🧙",
            "theme": "system",
            "created_at": "2024-01-01"
        }


def apply_global_styles():
    """Apply global CSS styles including bot card styles"""
    # Load bot card CSS
    bot_card_css = get_bot_card_css().strip()  # remove leading/trailing whitespace

    # FOUC prevention script (minimized — no indentation or newlines)
    fouc_prevention = """
<script>
document.addEventListener('DOMContentLoaded', function() {
  const style = document.createElement('style');
  style.textContent = '.portrait-card, .portrait-card-content, .portrait-card-name, .portrait-card-desc { visibility: hidden; }';
  document.head.appendChild(style);
  setTimeout(function() {
    document.querySelectorAll('.portrait-card, .portrait-card-content, .portrait-card-name, .portrait-card-desc')
      .forEach(el => el.style.visibility = 'visible');
  }, 100);
});
</script>
""".strip()

    # Combine safely
    html_block = f"<style>{bot_card_css}</style>{fouc_prevention}"

    # Inject into page
    st.markdown(html_block, unsafe_allow_html=True)


async def main():
    # Initialize application
    initialize_session_state()
    apply_global_styles()

    # Create sidebar navigation
    await create_sidebar()

    # Page routing
    if st.session_state.page == "home":
        await home_page()
    elif st.session_state.page == "profile":
        await profile_page()
    elif st.session_state.page == "chat":
        await chat_page(st.session_state.selected_bot)
    elif st.session_state.page == "bot_setup":
        await bot_setup_page()
    elif st.session_state.page == "generate_concept":
        await generate_concept_page()
    elif st.session_state.page == "create_bot":
        await create_bot_page()
    elif st.session_state.page == "my_bots":
        await my_bots_page()
    elif st.session_state.page == "edit_bot":
        await edit_bot_page()
    elif st.session_state.page == "voice":
        await voice_page()
    elif st.session_state.page == "image_studio":  # Add this condition
        await image_studio_page()
    elif st.session_state.page == "group_chat":
        await group_chat_page()
    else:
        st.warning("Please select a page")
        await home_page()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())