import streamlit as st
from controllers.chat_controller import LLMChatController
from components.audio_player import audio_player
from components.chat_toolbar import display_chat_toolbar
from components.avatar_utils import get_avatar_display
import pyperclip
from config import BOTS
import asyncio


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

    /* Copy and regenerate buttons */
    .stButton button[title="Copy this message"],
    .stButton button[title="Regenerate response"] {{
        background-color: rgba(255, 255, 255, 0.15) !important;
        font-size: 16px !important;
        padding: 0.25rem !important;
    }}

    /* Voice button specific styling */
    .stButton button[title="Generate audio"],
    .stButton button[title="Play audio"],
    .stButton button[title="Generating audio..."] {{
        background-color: rgba(255, 215, 0, 0.2) !important;
        font-size: 16px !important;
        padding: 0.25rem !important;
    }}

    .stButton button[title="Generate audio"]:hover,
    .stButton button[title="Play audio"]:hover {{
        background-color: rgba(255, 215, 0, 0.3) !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def _get_bot_details(bot_name):
    """Get the bot's details from session state"""
    # Check default bots (from config)
    default_bot = next((b for b in BOTS if b["name"] == bot_name), None)
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

    with st.chat_message(role, avatar=avatar if role == "assistant" else None):
        st.write(message)

        # Add copy and regenerate buttons for bot responses only (right-aligned)
        # But NOT for the first message (greeting)
        if role == "assistant" and idx > 0:  # Skip first message (greeting)
            await _display_message_actions(message, idx, chat_history, bot_name, bot_controller)

            # Voice button below the response (only if voice is enabled)
            if bot_has_voice and hasattr(st.session_state, 'voice_service'):
                _display_voice_button(message, current_bot, bot_name, idx)


async def _display_message_actions(message, idx, chat_history, bot_name, bot_controller):
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

        # Regenerate button - use direct async call instead of session state flag
        with action_cols[2]:
            if st.button(
                    "🔄",
                    key=f"regen_{bot_name}_{idx}",
                    help="Regenerate response",
                    use_container_width=True
            ):
                await _handle_regenerate_response_direct(idx, chat_history, bot_name, bot_controller)


async def _handle_regenerate_response_direct(idx, chat_history, bot_name, bot_controller):
    """Handle regenerate response directly without session state flags"""
    try:
        # Store the user message that prompted this response
        user_message = chat_history[idx - 1][1]  # Previous message is user input

        # Remove this response and all subsequent messages
        st.session_state.chat_histories[bot_name] = chat_history[:idx]

        # Clear memory of this exchange - this is crucial!
        if 'memory' in st.session_state:
            # Remove the last two messages from memory (user + assistant)
            messages = st.session_state.memory['chat_history'].messages
            if len(messages) >= 2:
                st.session_state.memory['chat_history'].messages = messages[:-2]

        # Clear audio cache for removed messages
        keys_to_remove = [key for key in st.session_state.audio_cache if
                          bot_name in key and int(key.split('_')[-1]) >= idx]
        for key in keys_to_remove:
            # Also remove the generating state if it exists
            generating_key = f"generating_{key}"
            if generating_key in st.session_state:
                del st.session_state[generating_key]
            del st.session_state.audio_cache[key]

        # Clear any regeneration flags that might be hanging around
        if hasattr(st.session_state, 'regenerate_requested'):
            del st.session_state.regenerate_requested

        # Regenerate response with fresh context
        with st.spinner("Regenerating response..."):
            # Generate new response - this should be different because memory was cleared
            new_response = await bot_controller.generate_single_response(user_message)
            st.session_state.chat_histories[bot_name].append(("assistant", new_response))

        # Force immediate rerun
        st.rerun()

    except Exception as e:
        st.error(f"Regeneration failed: {str(e)}")
        # Ensure we clear any stuck state
        if hasattr(st.session_state, 'regenerate_requested'):
            del st.session_state.regenerate_requested

async def _handle_regenerate_response():
    """Handle regenerate response functionality - called from main flow"""
    if not hasattr(st.session_state, 'regenerate_requested'):
        return

    request = st.session_state.regenerate_requested
    bot_name = request['bot_name']
    idx = request['message_idx']
    chat_history = request['chat_history']

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

    # Clear audio cache for removed messages
    keys_to_remove = [key for key in st.session_state.audio_cache if bot_name in key and int(key.split('_')[-1]) >= idx]
    for key in keys_to_remove:
        del st.session_state.audio_cache[key]

    # Regenerate response
    with st.spinner("Regenerating response..."):
        bot_controller = LLMChatController()  # Create new controller instance
        new_response = await bot_controller.generate_single_response(user_message)
        st.session_state.chat_histories[bot_name].append(("assistant", new_response))

    # Clear the regeneration request
    del st.session_state.regenerate_requested


def _handle_copy_message(message):
    """Handle copy message to clipboard"""
    try:
        pyperclip.copy(message)
        st.toast("Message copied to clipboard!", icon="📋")
    except Exception as e:
        st.error(f"Failed to copy: {str(e)}")

def _display_voice_button(message, current_bot, bot_name, idx):
    """Display voice generation button and audio player with three states"""
    try:
        # Create a unique key for this message's audio
        audio_key = f"audio_{bot_name}_{idx}"
        generating_key = f"generating_{audio_key}"

        # Initialize generating state if not exists
        if generating_key not in st.session_state:
            st.session_state[generating_key] = False

        # Check if audio already exists in cache
        audio_exists = audio_key in st.session_state.audio_cache
        import os

        if audio_exists:
            # Verify the file actually exists
            audio_path = st.session_state.audio_cache[audio_key]
            if not os.path.exists(audio_path):
                # Remove from cache if file doesn't exist
                del st.session_state.audio_cache[audio_key]
                audio_exists = False

        # Show appropriate button based on state
        if st.session_state[generating_key]:
            # Currently generating - show loading icon
            st.button("⏳", help="Generating audio...", key=f"loading_{audio_key}", disabled=True)
        elif audio_exists:
            # Audio exists - show play button
            audio_path = st.session_state.audio_cache[audio_key]
            if st.button("▶️", help="Play audio", key=f"play_{audio_key}"):
                # The audio_player will handle playback
                pass
            audio_player(audio_path, autoplay=False)
        else:
            # Audio doesn't exist - show generate button
            if st.button("🔊", help="Generate audio", key=f"generate_{audio_key}"):
                # Set generating state and generate audio asynchronously
                st.session_state[generating_key] = True
                asyncio.create_task(_generate_audio_for_message(message, current_bot, audio_key, generating_key))

    except Exception as e:
        st.error(f"Voice button error: {str(e)}")


async def _generate_audio_for_message(message, current_bot, audio_key, generating_key):
    """Generate audio for a specific message and update state"""
    try:
        emotion = current_bot["voice"]["emotion"]
        audio_path = st.session_state.voice_service.generate_speech(
            message,
            emotion,
            dialogue_only=True
        )

        if audio_path:
            # Cache the audio path and clear generating state
            st.session_state.audio_cache[audio_key] = audio_path
            st.session_state[generating_key] = False
            # Set flag to trigger rerun
            st.session_state.audio_generated = True
        else:
            st.error("Failed to generate audio")
            st.session_state[generating_key] = False

    except Exception as e:
        st.error(f"Voice generation failed: {str(e)}")
        st.session_state[generating_key] = False


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