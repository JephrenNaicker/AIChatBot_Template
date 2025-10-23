import streamlit as st

from components.avatar_utils import get_avatar_display
from components.chat_toolbar import display_chat_toolbar
from components.message_actions import display_message_actions, display_message_edit_interface, handle_pending_edit
from config import get_default_bots_dicts
from controllers.chat_controller import LLMChatController


async def chat_page(bot_name):
    """Chat page with the selected bot"""
    # Apply custom CSS for better visibility
    _apply_chat_styles()

    # Initialize controller and get bot details
    bot = LLMChatController()
    current_bot = _get_bot_details(bot_name)

    if not current_bot:
        _handle_bot_not_found()
        return

    # Initialize chat history and audio cache
    _initialize_chat_history(bot_name)
    _initialize_audio_cache()

    # Handle any pending message edits first
    await handle_pending_edit(bot)

    # Get current chat history
    chat_history = st.session_state.chat_histories[bot_name]

    # Display message editing interface if active
    display_message_edit_interface()

    # Display all messages
    await _display_messages(chat_history, current_bot, bot_name, bot)

    # Send greeting if first time
    await _send_greeting_if_needed(chat_history, current_bot, bot)

    # Display separator and main toolbar
    st.markdown("---")

    # Display input area and handle user input
    user_input = _display_input_area(bot_name)

    # Display the main toolbar
    await display_chat_toolbar(bot)

    # Handle user input
    if user_input:
        await _handle_user_input(user_input, chat_history, bot, bot_name)

    # Check if we need to rerun due to audio generation completion
    if st.session_state.get('audio_generated', False):
        st.session_state.audio_generated = False
        st.rerun()


def _apply_chat_styles():
    """Apply custom CSS styles for chat interface with dynamic gradients"""
    # Default colors (fallback)
    user_gradient = """
        linear-gradient(135deg, 
            rgba(30, 30, 60, 0.9) 0%, 
            rgba(50, 40, 80, 0.9) 50%,
            rgba(30, 30, 60, 0.9) 100%)
    """

    bot_gradient = """
        linear-gradient(135deg, 
            rgba(60, 30, 30, 0.9) 0%, 
            rgba(80, 40, 40, 0.9) 50%,
            rgba(60, 30, 30, 0.9) 100%)
    """

    st.markdown(f"""
    <style>
    /* Base chat message styling */
    .stChatMessage {{
        border-radius: 15px !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        background: rgba(0, 0, 0, 0.7) !important;
    }}

    /* Message text - white for contrast */
    .stChatMessage .stMarkdown {{
        color: white !important;
    }}

    /* User message specific styling */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {{
        background: {user_gradient} !important;
        border-left: 4px solid #6C8DFF !important;
        box-shadow: 2px 2px 10px rgba(76, 141, 255, 0.3) !important;
    }}

    /* Bot message specific styling */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {{
        background: {bot_gradient} !important;
        border-left: 4px solid #FF6B6B !important;
        box-shadow: 2px 2px 10px rgba(255, 107, 107, 0.3) !important;
    }}

    /* Chat input styling */
    .stChatInput {{
        background-color: rgba(0, 0, 0, 0.8) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}

    /* Main content area */
    .main .block-container {{
        background-color: rgba(0, 0, 0, 0.7) !important;
        border-radius: 15px !important;
        padding: 2rem !important;
        margin: 2rem !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }}

    /* Toolbar styling */
    .stContainer {{
        background-color: rgba(0, 0, 0, 0.8) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        backdrop-filter: blur(10px) !important;
    }}

    /* Button styling for better visibility */
    .stButton button {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
    }}

    .stButton button:hover {{
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }}

    /* Message action buttons */
    .stButton button[title^="Copy"],
    .stButton button[title^="Regenerate"],
    .stButton button[title^="Edit"],
    .stButton button[title^="Delete"],
    .stButton button[title^="Generate audio"],
    .stButton button[title^="Play audio"],
    .stButton button[title^="Generating audio"] {{
        background-color: rgba(255, 255, 255, 0.15) !important;
        font-size: 16px !important;
        padding: 0.25rem !important;
    }}

    .stButton button[title^="Generate audio"]:hover,
    .stButton button[title^="Play audio"]:hover {{
        background-color: rgba(255, 215, 0, 0.3) !important;
    }}

    /* NEW: Style for text in double quotes in bot messages */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) .stMarkdown p:has(> span[style*="color:"]),
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) .stMarkdown p:contains('"') {{
        /* This targets paragraphs containing quotes in bot messages */
    }}

    /* Style for quoted text specifically */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) .stMarkdown p {{
        position: relative;
    }}

    /* Color for text within double quotes in bot messages */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) .stMarkdown p:has(> span[style*="color:"]) {{
        color: #FFD700 !important; /* Gold color for quoted text */
    }}

    /* Alternative approach: target specific quote patterns */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) .stMarkdown p:contains('"') {{
        color: #FFD700 !important;
    }}

    /* More specific targeting for quoted dialogue */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) .stMarkdown p {{
        color: white !important; /* Default text color */
    }}

    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) .stMarkdown p:has(> span) {{
        color: inherit !important;
    }}

    /* Direct styling for spans that might contain quoted text */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) .stMarkdown span {{
        color: #FFD700 !important; /* Gold for spans in bot messages */
    }}

    /* Even more specific: target text between quotes using CSS attribute selectors */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) .stMarkdown p:not(:has(> span)) {{
        /* This will handle plain text quotes */
        color: white !important;
    }}

    /* Special class for quoted text - we'll add this via JavaScript or markdown */
    .quoted-text {{
        color: #FFD700 !important;
        font-style: italic;
    }}

    /* Target specific quote patterns in bot messages */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) .stMarkdown p:contains('"') {{
        color: #FFD700 !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def _get_bot_details(bot_name):
    """Get the bot's details from session state"""
    # Check default bots (from config)
    default_bot = next((b for b in get_default_bots_dicts() if b["name"] == bot_name), None)
    if default_bot:
        return default_bot

    # Check user bots
    user_bot = next((b for b in st.session_state.user_bots if b["name"] == bot_name), None)
    if user_bot:
        return user_bot

    return None


def _handle_bot_not_found():
    """Handle case when bot is not found"""
    st.error("Bot not found!")
    st.session_state.page = "my_bots"
    st.rerun()


def _initialize_chat_history(bot_name):
    """Initialize chat history for this bot if not exists"""
    if "chat_histories" not in st.session_state:
        st.session_state.chat_histories = {}

    if bot_name not in st.session_state.chat_histories:
        st.session_state.chat_histories[bot_name] = []

    if "greeting_sent" not in st.session_state:
        st.session_state.greeting_sent = False


def _initialize_audio_cache():
    """Initialize audio cache in session state"""
    if "audio_cache" not in st.session_state:
        st.session_state.audio_cache = {}

    if "audio_generated" not in st.session_state:
        st.session_state.audio_generated = False


async def _display_messages(chat_history, current_bot, bot_name, bot_controller):
    """Display all messages in the chat history"""
    bot_emoji = current_bot["emoji"] if current_bot else "🤖"
    bot_has_voice = current_bot.get("voice", {}).get("enabled", False) if current_bot else False

    for idx, (role, message) in enumerate(chat_history):
        await _display_single_message(
            role, message, idx, chat_history,
            current_bot, bot_name, bot_controller, bot_has_voice
        )


async def _display_single_message(role, message, idx, chat_history, current_bot,
                                  bot_name, bot_controller, bot_has_voice):
    """Display a single message with appropriate formatting and actions"""
    avatar = None
    if role == "assistant":
        avatar = get_avatar_display(current_bot, size=40)

    # Process message to style quoted text (for bot messages only)
    display_message = message
    if role == "assistant":
        # Wrap text in double quotes with gold color
        import re
        display_message = re.sub(
            r'"(.*?)"',
            r'<span style="color: #6ded82; font-style: italic;">"\1"</span>',
            message
        )

    with st.chat_message(role, avatar=avatar if role == "assistant" else None):
        if role == "assistant" and '"' in message:
            # Use markdown for styled text
            st.markdown(display_message, unsafe_allow_html=True)
        else:
            st.write(message)

        # Use the new message_actions component for all message actions
        await display_message_actions(
            role=role,
            message=message,
            idx=idx,
            chat_history=chat_history,
            bot_name=bot_name,
            bot_controller=bot_controller,
            bot_has_voice=bot_has_voice,
            current_bot=current_bot
        )


async def _send_greeting_if_needed(chat_history, current_bot, bot_controller):
    """Send greeting message if it's the first interaction"""
    if not st.session_state.greeting_sent or not chat_history:
        greeting = current_bot["personality"].get("greeting", "") if current_bot else ""
        if not greeting:
            greeting = await bot_controller.generate_greeting()

        chat_history.append(("assistant", greeting))
        bot_controller._process_memory("(System greeting)", greeting)
        st.session_state.greeting_sent = True
        st.rerun()


def _display_input_area(bot_name):
    """Display the input area with text input and voice button"""
    input_col1, input_col2 = st.columns([5, 1])

    with input_col1:
        user_input = st.chat_input("Type your message...", key=f"chat_input_{bot_name}")

    with input_col2:
        if st.button("🎤", help="Push to talk", key=f"voice_mic_{bot_name}", use_container_width=True):
            st.session_state.voice_input_active = True
            st.rerun()

    return user_input


async def _handle_user_input(user_input, chat_history, bot_controller, bot_name):
    """Handle user input and generate bot response"""
    chat_history.append(("user", user_input))
    with st.spinner(f"{bot_name} is thinking..."):
        response = await bot_controller.generate_single_response(user_input)
        chat_history.append(("assistant", response))
        st.rerun()