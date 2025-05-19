import streamlit as st
from controllers.group_chat_controller import GroupChatManager

def group_chat_page():
    if not st.session_state.group_chat['active']:
        GroupChatManager.show_group_setup()
    else:
        GroupChatManager.show_active_group_chat()