import streamlit as st
from controllers.chat_controller import LLMChatController

def chat_page(bot_name):
    """Chat page with the selected bot"""
    bot = LLMChatController()

    # Get the bot's details
    current_bot = next(
        (b for b in st.session_state.get('bots', []) + st.session_state.user_bots
         if b["name"] == bot_name),
        None
    )
    bot_emoji = current_bot["emoji"] if current_bot else "🤖"

    # Initialize chat history for this bot if not exists
    if bot_name not in st.session_state.chat_histories:
        st.session_state.chat_histories[bot_name] = []
        st.session_state.greeting_sent = False

    # Get current chat history
    chat_history = st.session_state.chat_histories[bot_name]

    # Display messages
    for role, message in chat_history:
        avatar = bot_emoji if role == "assistant" else None
        with st.chat_message(role, avatar=avatar):
            st.write(message)

    # Send greeting if first time
    if not st.session_state.greeting_sent or not chat_history:
        greeting = current_bot["personality"].get("greeting", "") if current_bot else ""
        if not greeting:
            greeting = bot.generate_greeting()

        chat_history.append(("assistant", greeting))
        st.session_state.greeting_sent = True
        st.rerun()

    # Add the icon toolbar at the bottom of the chat
    bot.display_chat_icon_toolbar()

    # User input handling
    if prompt := st.chat_input("Type your message..."):
        chat_history.append(("user", prompt))
        with st.spinner(f"{bot_name} is thinking..."):
            response = bot.generate_single_response(prompt)
            chat_history.append(("assistant", response))
            st.rerun()