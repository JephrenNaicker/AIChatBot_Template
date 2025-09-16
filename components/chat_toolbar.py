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