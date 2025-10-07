import streamlit as st
import pyperclip
import asyncio
from components.audio_player import audio_player


async def display_message_actions(role, message, idx, chat_history, bot_name, bot_controller, bot_has_voice,
                                  current_bot):
    """
    Display action buttons for a message (copy, regenerate, edit, delete, voice)

    Args:
        role: "user" or "assistant"
        message: The message content
        idx: Message index in chat history
        chat_history: Full chat history
        bot_name: Name of the current bot
        bot_controller: LLMChatController instance
        bot_has_voice: Whether voice is enabled for this bot
        current_bot: Bot details dictionary
    """
    try:
        # Different actions for user vs assistant messages
        if role == "assistant":
            await _display_assistant_actions(message, idx, chat_history, bot_name, bot_controller, bot_has_voice,
                                             current_bot)
        else:
            await _display_user_actions(message, idx, chat_history, bot_name, bot_controller)

    except Exception as e:
        st.error(f"Message actions error: {str(e)}")


async def _display_assistant_actions(message, idx, chat_history, bot_name, bot_controller, bot_has_voice, current_bot):
    """Display actions for assistant messages"""
    # Skip actions for greeting message
    if idx == 0:  # First message is usually greeting
        return

    with st.container():
        # Create columns for different action types
        action_cols = st.columns([4, 1, 1, 1])  # Space, copy, regenerate, voice

        # Empty space
        with action_cols[0]:
            st.empty()

        # Copy button
        with action_cols[1]:
            if st.button(
                    "📋",
                    help="Copy this message",
                    use_container_width=True,
                    key=f"copy_chat_{bot_name}_{idx}"
            ):
                _handle_copy_message(message)

        # Regenerate button
        with action_cols[2]:
            if st.button(
                    "🔄",
                    help="Regenerate response",
                    use_container_width=True,
                    key=f"regen_{bot_name}_{idx}"
            ):
                await _handle_regenerate_response(idx, chat_history, bot_name, bot_controller)

        # Voice button (only if voice is enabled)
        with action_cols[3]:
            if bot_has_voice and hasattr(st.session_state, 'voice_service'):
                _display_voice_button(message, current_bot, bot_name, idx)
            else:
                st.empty()  # Empty space if no voice


async def _display_user_actions(message, idx, chat_history, bot_name, bot_controller):
    """Display actions for user messages (edit, delete)"""
    with st.container():
        action_cols = st.columns([5, 1, 1])  # Space, edit, delete

        # Empty space
        with action_cols[0]:
            st.empty()

        # Edit button
        with action_cols[1]:
            if st.button(
                    "✏️",
                    help="Edit this message",
                    use_container_width=True,
                    key=f"edit_{bot_name}_{idx}"
            ):
                st.session_state.editing_message = {
                    'bot_name': bot_name,
                    'message_index': idx,
                    'current_content': message
                }
                st.rerun()

        # Delete button
        with action_cols[2]:
            if st.button(
                    "🗑️",
                    help="Delete this and subsequent messages",
                    use_container_width=True,
                    key=f"delete_{bot_name}_{idx}"
            ):
                await _handle_delete_message(idx, chat_history, bot_name, bot_controller)


def _handle_copy_message(message):
    """Handle copy message to clipboard"""
    try:
        pyperclip.copy(message)
        st.toast("Message copied to clipboard!", icon="📋")
    except Exception as e:
        st.error(f"Failed to copy: {str(e)}")


async def _handle_regenerate_response(idx, chat_history, bot_name, bot_controller):
    """Handle regenerate response for assistant messages"""
    try:
        # Store the user message that prompted this response
        user_message = chat_history[idx - 1][1]  # Previous message is user input

        # Remove this response and all subsequent messages
        st.session_state.chat_histories[bot_name] = chat_history[:idx]

        # Clear memory of this exchange
        if 'memory' in st.session_state:
            messages = st.session_state.memory['chat_history'].messages
            if len(messages) >= 2:
                st.session_state.memory['chat_history'].messages = messages[:-2]

        # Clear audio cache for removed messages
        keys_to_remove = [key for key in st.session_state.audio_cache if
                          bot_name in key and int(key.split('_')[-1]) >= idx]
        for key in keys_to_remove:
            generating_key = f"generating_{key}"
            if generating_key in st.session_state:
                del st.session_state[generating_key]
            del st.session_state.audio_cache[key]

        # Regenerate response
        with st.spinner("Regenerating response..."):
            new_response = await bot_controller.generate_single_response(user_message)
            st.session_state.chat_histories[bot_name].append(("assistant", new_response))

        st.rerun()

    except Exception as e:
        st.error(f"Regeneration failed: {str(e)}")


async def _handle_delete_message(idx, chat_history, bot_name, bot_controller):
    """Handle delete message and subsequent messages"""
    try:
        await bot_controller.delete_message(bot_name, idx)
        st.rerun()

    except Exception as e:
        st.error(f"Delete failed: {str(e)}")


def _display_voice_button(message, current_bot, bot_name, idx):
    """Display voice generation button with three states"""
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
                del st.session_state.audio_cache[audio_key]
                audio_exists = False

        # Show appropriate button based on state
        if st.session_state[generating_key]:
            st.button("⏳", help="Generating audio...", key=f"loading_{audio_key}", disabled=True)
        elif audio_exists:
            audio_path = st.session_state.audio_cache[audio_key]
            if st.button("▶️", help="Play audio", key=f"play_{audio_key}"):
                pass  # audio_player will handle playback
            audio_player(audio_path, autoplay=False)
        else:
            if st.button("🔊", help="Generate audio", key=f"generate_{audio_key}"):
                st.session_state[generating_key] = True
                asyncio.create_task(_generate_audio_for_message(message, current_bot, audio_key, generating_key))

    except Exception as e:
        st.error(f"Voice button error: {str(e)}")


async def _generate_audio_for_message(message, current_bot, audio_key, generating_key):
    """Generate audio for a specific message"""
    try:
        emotion = current_bot["voice"]["emotion"]
        audio_path = st.session_state.voice_service.generate_speech(
            message,
            emotion,
            dialogue_only=True
        )

        if audio_path:
            st.session_state.audio_cache[audio_key] = audio_path
            st.session_state[generating_key] = False
            st.session_state.audio_generated = True
        else:
            st.error("Failed to generate audio")
            st.session_state[generating_key] = False

    except Exception as e:
        st.error(f"Voice generation failed: {str(e)}")
        st.session_state[generating_key] = False


def display_message_edit_interface():
    """Display the message editing interface if editing is active"""
    if not hasattr(st.session_state, 'editing_message'):
        return None

    edit_data = st.session_state.editing_message

    st.markdown("---")
    st.subheader("✏️ Edit Message")

    edited_content = st.text_area(
        "Edit your message:",
        value=edit_data['current_content'],
        height=100,
        key="message_edit_textarea"
    )

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("💾 Save", use_container_width=True):
            # Save the edited message - DON'T delete editing_message yet
            st.session_state.editing_message['new_content'] = edited_content
            st.session_state.editing_message['action'] = 'save'
            # DON'T delete st.session_state.editing_message here
            st.rerun()

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            # Cancel editing - only delete on cancel
            del st.session_state.editing_message
            st.rerun()

    with col3:
        st.info("Editing this message will delete all subsequent messages.")

    return edited_content


async def handle_pending_edit(bot_controller):
    """Handle any pending edit operations"""
    if not hasattr(st.session_state, 'editing_message'):
        return

    edit_data = st.session_state.editing_message
    print(f"DEBUG: Processing edit - action: {edit_data.get('action')}, has new_content: {'new_content' in edit_data}")

    if edit_data.get('action') == 'save' and 'new_content' in edit_data:
        try:
            print(f"DEBUG: Starting edit for message {edit_data['message_index']} in {edit_data['bot_name']}")

            # Apply the edit
            await bot_controller.edit_user_message(
                edit_data['bot_name'],
                edit_data['message_index'],
                edit_data['new_content']
            )

            print(f"DEBUG: Edit applied, regenerating response")

            # Regenerate the response
            await bot_controller.regenerate_after_edit(
                edit_data['bot_name'],
                edit_data['message_index']
            )

            st.toast("Message updated and response regenerated!", icon="✅")
            print(f"DEBUG: Edit completed successfully")

        except Exception as e:
            st.error(f"Edit failed: {str(e)}")
            print(f"DEBUG: Edit failed with error: {str(e)}")

        # Clear the edit state
        if 'editing_message' in st.session_state:
            del st.session_state.editing_message
            print(f"DEBUG: Cleared editing_message from session state")