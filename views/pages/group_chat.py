import streamlit as st
from controllers.group_chat_controller import GroupChatManager

async def group_chat_page():
    chat_manager = GroupChatManager()  # Create instance
    if not st.session_state.group_chat['active']:
        await chat_manager.show_group_setup()
    else:
        await chat_manager.show_active_group_chat()