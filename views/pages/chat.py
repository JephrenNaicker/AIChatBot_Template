import streamlit as st
from controllers.chat_controller import LLMChatController
from components.audio_player import audio_player
from components.chat_toolbar import display_chat_toolbar


async def chat_page(bot_name):
    """Chat page with the selected bot"""
    bot = LLMChatController()

    # Get the bot's details
    current_bot = next(
        (b for b in st.session_state.get('bots', []) + st.session_state.user_bots
         if b["name"] == bot_name),
        None
    )

    # Debug bot info
    with st.expander("Bot Debug Info", expanded=False):
        if current_bot:
            st.write("Current bot:", current_bot["name"])
            st.write("Bot voice settings:", current_bot.get("voice", "NO VOICE SETTINGS"))
            st.write("Bot has voice enabled:", current_bot.get("voice", {}).get("enabled", False))
            if "voice" in current_bot:
                st.write("Voice emotion:", current_bot["voice"].get("emotion"))
        else:
            st.error("Current bot not found!")


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
        avatar = bot_emoji if role == "assistant" else None
        with st.chat_message(role, avatar=avatar):
            st.write(message)

            # Add voice button below bot responses
            if role == "assistant" and bot_has_voice and hasattr(st.session_state, 'voice_service'):
                # Create a container for the voice button
                with st.container():
                    cols = st.columns([1, 4])
                    with cols[0]:
                        if st.button(
                                "🔊 Play",
                                key=f"voice_btn_{idx}",
                                help="Play this message with voice"
                        ):
                            try:
                                emotion = current_bot["voice"]["emotion"]
                                audio_path = st.session_state.voice_service.generate_speech(
                                    message,
                                    emotion,
                                    dialogue_only=True #
                                )
                                if audio_path:
                                    # Display the audio player
                                    with cols[1]:
                                        audio_player(audio_path, autoplay=True)
                            except Exception as e:
                                st.error(f"Voice generation failed: {str(e)}")

    # Send greeting if first time
    if not st.session_state.greeting_sent or not chat_history:
        greeting = current_bot["personality"].get("greeting", "") if current_bot else ""
        if not greeting:
            greeting = await bot.generate_greeting()

        chat_history.append(("assistant", greeting))
        bot._process_memory("(System greeting)", greeting)  # Add this line
        st.session_state.greeting_sent = True
        st.rerun()

    # Add the icon toolbar at the bottom of the chat
    await display_chat_toolbar(bot)

    # User input handling
    if prompt := st.chat_input("Type your message..."):
        chat_history.append(("user", prompt))
        with st.spinner(f"{bot_name} is thinking..."):
            response = await bot.generate_single_response(prompt)
            chat_history.append(("assistant", response))
            st.rerun()