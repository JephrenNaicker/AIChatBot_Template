import streamlit as st
import pyperclip
from controllers.chat_controller import LLMChatController


async def display_chat_toolbar(controller: LLMChatController = None):
    """Standalone chat toolbar component"""
    if controller is None:
        controller = LLMChatController()

    with st.container():
        # Create columns for the toolbar layout
        left_group, center_spacer, right_options = st.columns([4, 2, 2])

        with left_group:
            # Action buttons in a horizontal layout
            action_cols = st.columns(4)
            with action_cols[0]:
                if st.button(
                        "🖼️",
                        help="Generate image based on conversation",
                        key="img_gen_btn"
                ):
                    st.toast("Image generation coming soon!", icon="🖼️")

            with action_cols[1]:
                if st.button(
                        "🎙️",
                        help="Enable voice input",
                        key="voice_input_btn"
                ):
                    st.toast("Voice input coming soon!", icon="🎙️")

            with action_cols[2]:
                # Get current chat history length
                chat_history = st.session_state.chat_histories.get(
                    st.session_state.selected_bot, []
                )
                disabled = len(chat_history) < 2  # Need at least 1 exchange to regenerate

                if st.button(
                        "🔄",
                        help="Regenerate bot's last response",
                        disabled=disabled,
                        key="regenerate_btn"
                ):
                    if not disabled:
                        try:
                            with st.spinner("Re-generating response..."):
                                # 1. Remove the last bot response from history
                                chat_history.pop()  # We don't need to store this in a variable
                                last_user_msg = chat_history[-1][1]  # Get last user message

                                # 2. Clear the memory of the last exchange
                                controller.clear_last_exchange()

                                # 3. Generate fresh response
                                new_response = await controller.generate_single_response(last_user_msg)

                                # 4. Update history
                                chat_history.append(("assistant", new_response))
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to regenerate: {str(e)}")
                            st.rerun()

            with action_cols[3]:
                if st.button(
                        "📋",
                        help="Copy chat history to clipboard",
                        key="copy_chat_btn"
                ):
                    try:
                        chat_text = "\n".join(
                            f"{role}: {msg}" for role, msg in chat_history
                        )
                        pyperclip.copy(chat_text)
                        st.toast("Chat copied to clipboard!", icon="📋")
                    except Exception as e:
                        st.error(f"Failed to copy: {str(e)}")

        with right_options:
            # More options dropdown
            with st.popover("⚙️", help="More options"):
                # Clear chat confirmation flow
                if 'confirm_clear' not in st.session_state:
                    st.session_state.confirm_clear = False

                if st.button(
                        "🗑️ Clear Chat",
                        help="Start a fresh conversation",
                        use_container_width=True,
                        key="clear_chat_main"
                ):
                    st.session_state.confirm_clear = True

                if st.session_state.confirm_clear:
                    st.warning("This will erase all messages in this chat.")
                    confirm_cols = st.columns(2)
                    with confirm_cols[0]:
                        if st.button(
                                "✅ Confirm",
                                type="primary",
                                use_container_width=True,
                                key="confirm_clear_yes"
                        ):
                            bot_name = st.session_state.selected_bot
                            st.session_state.chat_histories[bot_name] = []
                            st.session_state.greeting_sent = False
                            st.session_state.confirm_clear = False
                            st.toast("Chat cleared!", icon="🗑️")
                            st.rerun()
                    with confirm_cols[1]:
                        if st.button(
                                "❌ Cancel",
                                use_container_width=True,
                                key="confirm_clear_no"
                        ):
                            st.session_state.confirm_clear = False
                            st.rerun()

                st.divider()

                # Additional options
                st.caption("Advanced Options")
                if st.button(
                        "💾 Export Chat",
                        disabled=True,
                        help="Export conversation history (coming soon)",
                        use_container_width=True
                ):
                    st.toast("Export feature coming soon!", icon="💾")

                if st.button(
                        "🔄 Switch Bot",
                        disabled=True,
                        help="Change character mid-conversation (coming soon)",
                        use_container_width=True
                ):
                    st.toast("Bot switching coming soon!", icon="🔄")