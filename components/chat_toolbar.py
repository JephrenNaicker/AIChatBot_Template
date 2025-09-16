import streamlit as st
import pyperclip
from controllers.chat_controller import LLMChatController


async def display_chat_toolbar(controller: LLMChatController = None):
    """Compact chat toolbar component"""
    if controller is None:
        controller = LLMChatController()

    # Get current chat history
    bot_name = st.session_state.selected_bot
    chat_history = st.session_state.chat_histories.get(bot_name, [])

    # Create a compact toolbar (image, options, spacer)
    toolbar_cols = st.columns([1, 1, 4])

    # Image generation button
    with toolbar_cols[0]:
        if st.button(
                "🖼️",
                help="Generate image based on conversation",
                key=f"img_gen_{bot_name}",
                use_container_width=True
        ):
            st.toast("Image generation coming soon!", icon="🖼️")

    # More options dropdown
    with toolbar_cols[1]:
        with st.popover("⚙️"):
            # Clear chat option
            if st.button(
                    "🗑️ Clear Chat",
                    help="Start a fresh conversation",
                    use_container_width=True,
                    key=f"clear_chat_{bot_name}"
            ):
                st.session_state.chat_histories[bot_name] = []
                st.session_state.greeting_sent = False
                if 'memory' in st.session_state:
                    st.session_state.memory['chat_history'].clear()
                st.toast("Chat cleared!", icon="🗑️")
                st.rerun()

            st.divider()

            # Regenerate last response option
            disabled = len(chat_history) < 2  # Need at least 1 exchange (greeting + user + response)
            if st.button(
                    "🔄 Regenerate Last",
                    help="Regenerate bot's last response",
                    disabled=disabled,
                    use_container_width=True,
                    key=f"regen_last_{bot_name}"
            ):
                if not disabled:
                    try:
                        # Find the last bot response (skip the greeting if it's the only one)
                        last_bot_idx = None
                        for i in range(len(chat_history) - 1, -1, -1):
                            if chat_history[i][0] == "assistant" and i > 0:  # Skip greeting
                                last_bot_idx = i
                                break

                        if last_bot_idx is not None:
                            user_message = chat_history[last_bot_idx - 1][1]

                            # Remove everything after the user message
                            st.session_state.chat_histories[bot_name] = chat_history[:last_bot_idx]

                            # Clear memory of this exchange
                            if 'memory' in st.session_state:
                                messages = st.session_state.memory['chat_history'].messages
                                if len(messages) >= 2:
                                    st.session_state.memory['chat_history'].messages = messages[:-2]

                            # Regenerate response
                            with st.spinner("Regenerating response..."):
                                new_response = await controller.generate_single_response(user_message)
                                st.session_state.chat_histories[bot_name].append(("assistant", new_response))

                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed to regenerate: {str(e)}")

            st.divider()

            # Export chat option
            if st.button(
                    "💾 Export Chat",
                    help="Export conversation history",
                    use_container_width=True,
                    key=f"export_chat_{bot_name}"
            ):
                chat_text = f"Chat with {bot_name}\n\n"
                for role, msg in chat_history:
                    prefix = "You: " if role == "user" else f"{bot_name}: "
                    chat_text += f"{prefix}{msg}\n\n"

                st.download_button(
                    "Download chat",
                    chat_text,
                    file_name=f"chat_with_{bot_name}.txt",
                    mime="text/plain",
                    key=f"download_{bot_name}"
                )