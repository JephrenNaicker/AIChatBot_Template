import streamlit as st
from controllers.chat_controller import LLMChatController
from components.audio_player import audio_player
from components.chat_toolbar import display_chat_toolbar
from components.avatar_utils import get_avatar_display
import pyperclip

async def chat_page(bot_name):
    """Chat page with the selected bot"""
    bot = LLMChatController()

    # Get the bot's details
    current_bot = next(
        (b for b in st.session_state.get('bots', []) + st.session_state.user_bots
         if b["name"] == bot_name),
        None
    )

    if not current_bot:
        st.error("Bot not found!")
        st.session_state.page = "my_bots"
        st.rerun()
        return

    bot_emoji = current_bot["emoji"] if current_bot else "🤖"
    bot_has_voice = current_bot.get("voice", {}).get("enabled", False) if current_bot else False

    # Initialize chat history for this bot if not exists
    if bot_name not in st.session_state.chat_histories:
        st.session_state.chat_histories[bot_name] = []
        st.session_state.greeting_sent = False

    # Get current chat history
    chat_history = st.session_state.chat_histories[bot_name]

    # Display messages
    for idx, (role, message) in enumerate(chat_history):
        # Get avatar for bot messages
        avatar = None
        if role == "assistant":
            avatar = get_avatar_display(current_bot, size=40)

        with st.chat_message(role, avatar=avatar if role == "assistant" else None):
            st.write(message)

            # Add copy and regenerate buttons for bot responses only (right-aligned)
            # But NOT for the first message (greeting)
            if role == "assistant" and idx > 0:  # Skip first message (greeting)
                # Create a container for the action buttons
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
                            try:
                                pyperclip.copy(message)  # <-- copy only this block
                                st.toast("Message copied to clipboard!", icon="📋")
                            except Exception as e:
                                st.error(f"Failed to copy: {str(e)}")

                    # Regenerate button
                    with action_cols[2]:
                        if st.button(
                                "🔄",
                                key=f"regen_{bot_name}_{idx}",
                                help="Regenerate response",
                                use_container_width=True
                        ):
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
                                new_response = await bot.generate_single_response(user_message)
                                st.session_state.chat_histories[bot_name].append(("assistant", new_response))

                            st.rerun()

                # Voice button below the response (only if voice is enabled)
                if bot_has_voice and hasattr(st.session_state, 'voice_service'):
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

    # Send greeting if first time
    if not st.session_state.greeting_sent or not chat_history:
        greeting = current_bot["personality"].get("greeting", "") if current_bot else ""
        if not greeting:
            greeting = await bot.generate_greeting()

        chat_history.append(("assistant", greeting))
        bot._process_memory("(System greeting)", greeting)
        st.session_state.greeting_sent = True
        st.rerun()

    # Display separator and main toolbar
    st.markdown("---")

    # Input area with voice button
    input_col1, input_col2 = st.columns([5, 1])

    with input_col1:
        user_input = st.chat_input("Type your message...", key=f"chat_input_{bot_name}")

    with input_col2:
        if st.button("🎤", help="Push to talk", key=f"voice_mic_{bot_name}", use_container_width=True):
            st.session_state.voice_input_active = True
            st.rerun()

    # Display the main toolbar below the input
    await display_chat_toolbar(bot)

    if user_input:
        chat_history.append(("user", user_input))
        with st.spinner(f"{bot_name} is thinking..."):
            response = await bot.generate_single_response(user_input)
            chat_history.append(("assistant", response))
            st.rerun()