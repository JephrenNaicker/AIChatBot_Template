import streamlit as st
from controllers.group_chat_controller import GroupChatManager

async def group_chat_page():
    if not st.session_state.group_chat['active']:
        await GroupChatManager.show_group_setup()
    else:
        await GroupChatManager.show_active_group_chat()