import streamlit as st
from controllers.chat_controller import LLMChatController
from components.audio_player import audio_player
from components.chat_toolbar import display_chat_toolbar
from components.avatar_utils import get_avatar_display
import pyperclip


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

    # Initialize chat history
    _initialize_chat_history(bot_name)

    # Get current chat history
    chat_history = st.session_state.chat_histories[bot_name]

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


def _apply_chat_styles():
    """Apply custom CSS styles for chat interface"""
    st.markdown("""
    <style>
    /* Chat message containers - translucent dark background */
    .stChatMessage {
        background-color: rgba(0, 0, 0, 0.7) !important;
        border-radius: 15px !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
    }

    /* Message text - white for contrast */
    .stChatMessage .stMarkdown {
        color: white !important;
    }

    /* User message specific styling */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: rgba(30, 30, 60, 0.8) !important;
        border-left: 4px solid #4F8BF9 !important;
    }

    /* Bot message specific styling */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: rgba(60, 30, 30, 0.8) !important;
        border-left: 4px solid #FF4B4B !important;
    }

    /* Chat input styling */
    .stChatInput {
        background-color: rgba(0, 0, 0, 0.8) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* Main content area */
    .main .block-container {
        background-color: rgba(0, 0, 0, 0.7) !important;
        border-radius: 15px !important;
        padding: 2rem !important;
        margin: 2rem !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Toolbar styling */
    .stContainer {
        background-color: rgba(0, 0, 0, 0.8) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        backdrop-filter: blur(10px) !important;
    }

    /* Button styling for better visibility */
    .stButton button {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
    }

    .stButton button:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }

    /* Copy and regenerate buttons */
    .stButton button[title="Copy this message"],
    .stButton button[title="Regenerate response"] {
        background-color: rgba(255, 255, 255, 0.15) !important;
        font-size: 16px !important;
        padding: 0.25rem !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ... (rest of the methods remain the same as in the previous version)
def _get_bot_details(bot_name):
    """Get the bot's details from session state"""
    return next(
        (b for b in st.session_state.get('bots', []) + st.session_state.user_bots
         if b["name"] == bot_name),
        None
    )


def _handle_bot_not_found():
    """Handle case when bot is not found"""
    st.error("Bot not found!")
    st.session_state.page = "my_bots"
    st.rerun()


def _initialize_chat_history(bot_name):
    """Initialize chat history for this bot if not exists"""
    if bot_name not in st.session_state.chat_histories:
        st.session_state.chat_histories[bot_name] = []
        st.session_state.greeting_sent = False


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

    with st.chat_message(role, avatar=avatar if role == "assistant" else None):
        st.write(message)

        # Add copy and regenerate buttons for bot responses only (right-aligned)
        # But NOT for the first message (greeting)
        if role == "assistant" and idx > 0:  # Skip first message (greeting)
            _display_message_actions(message, idx, chat_history, bot_name, bot_controller)

            # Voice button below the response (only if voice is enabled)
            if bot_has_voice and hasattr(st.session_state, 'voice_service'):
                _display_voice_button(message, current_bot)


def _display_message_actions(message, idx, chat_history, bot_name, bot_controller):
    """Display copy and regenerate buttons for a message"""
    with st.container():
        action_cols = st.columns([6, 1, 1])  # Message space, copy, regenerate

        # Empty space to push buttons to the right
        with action_cols[0]:
            st.empty()

        # Copy button
        with action_cols[1]:
            if st.button(
                    "📋",
                    help="Copy this message",
                    use_container_width=True,
                    key=f"copy_chat_{bot_name}_{idx}"  # unique key per message
            ):
                _handle_copy_message(message)

        # Regenerate button
        with action_cols[2]:
            if st.button(
                    "🔄",
                    key=f"regen_{bot_name}_{idx}",
                    help="Regenerate response",
                    use_container_width=True
            ):
                _handle_regenerate_response(idx, chat_history, bot_name, bot_controller)


def _handle_copy_message(message):
    """Handle copy message to clipboard"""
    try:
        pyperclip.copy(message)
        st.toast("Message copied to clipboard!", icon="📋")
    except Exception as e:
        st.error(f"Failed to copy: {str(e)}")


async def _handle_regenerate_response(idx, chat_history, bot_name, bot_controller):
    """Handle regenerate response functionality"""
    # Store the user message that prompted this response
    user_message = chat_history[idx - 1][1]  # Previous message is user input

    # Remove this response and all subsequent messages
    st.session_state.chat_histories[bot_name] = chat_history[:idx]

    # Clear memory of this exchange
    if 'memory' in st.session_state:
        # Remove the last two messages from memory (user + assistant)
        messages = st.session_state.memory['chat_history'].messages
        if len(messages) >= 2:
            st.session_state.memory['chat_history'].messages = messages[:-2]

    # Regenerate response
    with st.spinner("Regenerating response..."):
        new_response = await bot_controller.generate_single_response(user_message)
        st.session_state.chat_histories[bot_name].append(("assistant", new_response))

    st.rerun()


def _display_voice_button(message, current_bot):
    """Display voice generation button and audio player"""
    try:
        emotion = current_bot["voice"]["emotion"]
        audio_path = st.session_state.voice_service.generate_speech(
            message,
            emotion,
            dialogue_only=True
        )
        if audio_path:
            # Display audio player below the response
            audio_player(audio_path, autoplay=False)
    except Exception as e:
        st.error(f"Voice generation failed: {str(e)}")


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